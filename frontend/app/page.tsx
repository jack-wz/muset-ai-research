export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold">Muset AI Writing Assistant</h1>
        <p className="text-xl text-gray-600">
          Intelligent writing assistant powered by AI
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
          >
            Get Started
          </a>
          <a
            href="/docs"
            className="rounded-lg border border-gray-300 px-6 py-3 hover:bg-gray-50"
          >
            Documentation
          </a>
        </div>
      </main>
    </div>
  );
}
