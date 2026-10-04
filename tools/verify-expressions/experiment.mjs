// Evidence check for the injection cases (see docs/evidence-audit.md).
//
// For each case, evaluate its expression with GitHub's own published expression engine
// (@actions/expressions), put the result into the script text the way GitHub does before the shell
// runs, run that script in bash, and report whether a harmless canary file (touch) appeared. Each case
// has its own canary, deleted first, so one success can never make a later check pass by accident.
// Clean twins must NOT run the payload. The process exits non-zero if any result differs from what the
// corpus labels claim, so this doubles as a regression check.
//
// Limits: @actions/expressions is one of several implementations of the language (the runner's C# code
// is the reference), and the substitution step is modeled from GitHub's documentation, not observed on
// a live runner. Everything runs inside a throwaway directory; the only side effect is `touch`.
import { Parser, Lexer, Evaluator, data } from "@actions/expressions";
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const WORK = mkdtempSync(path.join(tmpdir(), "actionsbench-expr-"));
mkdirSync(WORK, { recursive: true });

function toData(value) {
  if (typeof value === "string") return new data.StringData(value);
  if (typeof value === "number") return new data.NumberData(value);
  if (typeof value === "boolean") return new data.BooleanData(value);
  // The Dictionary constructor takes rest arguments (the package README's array example is wrong).
  return new data.Dictionary(...Object.entries(value).map(([key, v]) => ({ key, value: toData(v) })));
}

function evaluate(expression, contexts) {
  const lexed = new Lexer(expression).lex();
  const parser = new Parser(lexed.tokens, Object.keys(contexts), []);
  return new Evaluator(parser.parse(), toData(contexts)).evaluate().coerceString();
}

// A title may contain spaces; a git ref name may not, so ref payloads use ${IFS}, as the real-world
// Ultralytics branch name did.
const titlePayload = (canary) => `x$(touch ${canary})`;
const refPayload = (canary) => `x$(touch\${IFS}${canary})`;

const rows = [];
function run({ id, expression, contexts, template, payload, expectInjection }) {
  const canary = `canary_${id.replace(/[^A-Za-z0-9]/g, "_")}`;
  const canaryPath = path.join(WORK, canary);
  rmSync(canaryPath, { force: true });
  const evaluated = evaluate(expression, contexts(payload(canary)));
  const script = template.replace("{{EXPR}}", evaluated);
  const result = spawnSync("bash", ["-c", script], { cwd: WORK, encoding: "utf8" });
  const injected = existsSync(canaryPath);
  rows.push({
    case: id,
    "evaluated expression": evaluated.length > 52 ? evaluated.slice(0, 49) + "..." : evaluated,
    "payload ran": injected,
    expected: expectInjection,
    ok: injected === expectInjection,
    exit: result.status,
  });
}

const PR = (title) => ({
  github: {
    event: { pull_request: { title, number: 42 } },
    sha: "0123456789abcdef0123456789abcdef01234567",
  },
});

// ---- positives: the payload must run
run({ id: "AB-INJ-0001 format()", expression: "format('Title is {0}', github.event.pull_request.title)", contexts: PR, template: "echo {{EXPR}}", payload: titlePayload, expectInjection: true });
run({
  id: "AB-INJ-0002 contains()&&",
  expression: "contains(github.ref, 'refs/pull/') && github.head_ref",
  contexts: (p) => ({ github: { ref: "refs/pull/7/merge", head_ref: p } }),
  template: "echo {{EXPR}}",
  payload: refPayload,
  expectInjection: true,
});
run({ id: "AB-INJ-0003 toJSON()", expression: "toJSON(github.event.pull_request.title)", contexts: PR, template: "echo {{EXPR}}", payload: titlePayload, expectInjection: true });
run({
  id: "AB-INJ-0004 ref_name",
  expression: "github.ref_name",
  contexts: (p) => ({ github: { ref_name: p } }),
  template: 'echo "Building {{EXPR}}"',
  payload: refPayload,
  expectInjection: true,
});
run({
  id: "AB-INJ-0005 author name",
  expression: "github.event.head_commit.author.name",
  contexts: (p) => ({ github: { event: { head_commit: { author: { name: p } } } } }),
  template: 'echo "Author is {{EXPR}}"',
  payload: titlePayload,
  expectInjection: true,
});
run({
  id: "AB-INJ-0007 composite input",
  expression: "inputs.title",
  contexts: (p) => ({ inputs: { title: p } }),
  template: "echo {{EXPR}}",
  payload: titlePayload,
  expectInjection: true,
});
run({
  id: "AB-INJ-0008 deep line",
  expression: "github.event.pull_request.title",
  contexts: PR,
  template: 'echo "Starting report"\necho "Title: {{EXPR}}"\necho "Done"',
  payload: titlePayload,
  expectInjection: true,
});
run({
  id: "AB-INJ-0009 issue title",
  expression: "github.event.issue.title",
  contexts: (p) => ({ github: { event: { issue: { title: p } } } }),
  template: 'echo "New issue {{EXPR}}"',
  payload: titlePayload,
  expectInjection: true,
});
run({
  id: "AB-INJ-0010 review comment",
  expression: "github.event.comment.body",
  contexts: (p) => ({ github: { event: { comment: { body: p } } } }),
  template: 'echo "Comment {{EXPR}}"',
  payload: titlePayload,
  expectInjection: true,
});

// ---- clean twins: nothing may run
run({ id: "AB-NEG-0002 boolean contains", expression: "!contains(github.event.pull_request.title, 'WIP')", contexts: PR, template: "echo {{EXPR}}", payload: titlePayload, expectInjection: false });
run({ id: "AB-NEG-0012 pr number", expression: "github.event.pull_request.number", contexts: PR, template: "echo {{EXPR}}", payload: titlePayload, expectInjection: false });
run({ id: "AB-NEG-0012 sha", expression: "github.sha", contexts: PR, template: "echo {{EXPR}}", payload: titlePayload, expectInjection: false });

// AB-NEG-0001 / AB-NEG-0011: the value reaches the shell through an environment variable, not the script
{
  const canary = "canary_env";
  const canaryPath = path.join(WORK, canary);
  rmSync(canaryPath, { force: true });
  const r = spawnSync("bash", ["-c", 'echo "$TITLE"'], {
    cwd: WORK,
    encoding: "utf8",
    env: { ...process.env, TITLE: titlePayload(canary) },
  });
  const injected = existsSync(canaryPath);
  rows.push({
    case: "AB-NEG-0001/0011 env var",
    "evaluated expression": r.stdout.trim(),
    "payload ran": injected,
    expected: false,
    ok: injected === false,
    exit: r.status,
  });
}

console.table(rows);

// Is the branch-name payload a legal git ref? (Ref names cannot contain spaces, hence ${IFS}.)
const refName = refPayload("canary");
let refLegal = false;
try {
  execFileSync("git", ["check-ref-format", "--branch", refName], { encoding: "utf8" });
  refLegal = true;
} catch {
  refLegal = false;
}
console.log(`git accepts the branch name ${JSON.stringify(refName)}: ${refLegal ? "yes" : "NO"}`);

rmSync(WORK, { recursive: true, force: true });
const failed = rows.filter((r) => !r.ok);
if (failed.length > 0 || !refLegal) {
  console.error(`MISMATCH: ${failed.map((r) => r.case).join(", ") || "branch name not a legal ref"}`);
  process.exitCode = 1;
} else {
  console.log("all results match the corpus labels");
}
