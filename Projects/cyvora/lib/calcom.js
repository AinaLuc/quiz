export async function fetchCalcomEventTypes(apiKey) {
  if (!apiKey) {
    throw new Error("Missing Cal.com API key");
  }

  const response = await fetch("https://api.cal.com/v2/event-types", {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "cal-api-version": "2024-08-13" // Standard API version for v2
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Invalid Cal.com API key");
    }
    throw new Error(`Failed to fetch Cal.com event types: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Cal.com v2 API typically returns { status: "success", data: [...] }
  return data.data || [];
}
