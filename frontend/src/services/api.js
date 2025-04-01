const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  console.error("Error: VITE_API_BASE_URL environment variable is not set.");
}

/**
 * Searches for operators via the API.
 * @param {string} query - The search term.
 * @param {number} limit - Max number of results per page.
 * @param {number} offset - Number of results to skip.
 * @returns {Promise<object>} - A promise that resolves to the API response { total_count, results }
 * @throws {Error} - Throws an error if the fetch fails or API returns an error status.
 */
export async function searchOperators(query, limit = 20, offset = 0) {
  // Construct the full URL with query parameters
  const searchParams = new URLSearchParams({
    q: query,
    limit: limit.toString(),
    offset: offset.toString(),
  });
  const url = `${API_BASE_URL}/operators/search?${searchParams.toString()}`;

  console.log(`Fetching: ${url}`); // Log the URL for debugging

  try {
    const response = await fetch(url);

    if (!response.ok) {
      // Try to get error details from response body if possible
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // Ignore if response body is not JSON
      }
      console.error("API Error Response:", errorData);
      throw new Error(
        `API request failed with status ${response.status}: ${
          errorData?.detail || response.statusText
        }`
      );
    }

    // Parse the JSON response
    const data = await response.json();
    return data; // Should be { total_count: number, results: array }
  } catch (error) {
    console.error("Error during API call:", error);
    // Re-throw the error to be caught by the component
    throw error;
  }
}