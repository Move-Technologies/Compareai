import React from "react";

export async function fetchRevenue() {
  try {
    // We artificially delay a response for demo purposes.
    // Don't do this in production :)
    console.log("Fetching revenue data...");
    await new Promise((resolve) => setTimeout(resolve, 10000));

    // const data = await sql<Revenue>`SELECT * FROM revenue`;

    console.log("Data fetch completed after 5 seconds.");
    return;
    // return data.rows;
  } catch (error) {
    console.error("Database Error:", error);
    throw new Error("Failed to fetch revenue data.");
  }
}
async function test() {
  const data = await fetchRevenue();
  console.log(
    "thissssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss"
  );
  return <div>test</div>;
}

export default test;
