import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { query, n_results = 8 } = body;

    if (!query || !query.trim()) {
      return NextResponse.json({ error: "Query is required" }, { status: 400 });
    }

    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    
    console.log(`Forwarding recommendation request to ${backendUrl}/recommend/ with query: "${query}"`);

    const response = await fetch(`${backendUrl}/recommend/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query.trim(),
        n_results: Number(n_results),
      }),
      // Set a short cache lifetime or disable caching to ensure fresh results
      cache: "no-store",
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`Backend API error response: status ${response.status}, text: ${errText}`);
      return NextResponse.json(
        { error: `Backend API error (${response.status}): ${errText || "Unknown error"}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Fetch request to FastAPI backend failed:", error);
    return NextResponse.json(
      { error: `Failed to connect to recommendation engine: ${error.message || "Connection refused"}` },
      { status: 502 } // Bad Gateway
    );
  }
}
