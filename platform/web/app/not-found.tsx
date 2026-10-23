import Link from "next/link";

export default function NotFound() {
  return (
    <div className="hero">
      <h1>Nothing here</h1>
      <p className="lede">The page you asked for does not exist on this platform.</p>
      <div className="chips">
        <Link className="chip" href="/">Home</Link>
        <Link className="chip" href="/cases">All cases</Link>
        <Link className="chip" href="/results">Results</Link>
      </div>
    </div>
  );
}
