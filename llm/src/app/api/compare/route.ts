import { NextResponse } from "next/server";
import OpenAI from "openai";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file1 = formData.get("file1") as File;
    const file2 = formData.get("file2") as File;
    const apiKey = formData.get("apiKey") as string;

    if (!file1 || !file2 || !apiKey) {
      return NextResponse.json(
        { error: "Missing required files or API key" },
        { status: 400 }
      );
    }

    const openai = new OpenAI({ apiKey });

    // Convert files to text
    const text1 = await file1.text();
    const text2 = await file2.text();

    // Parse documents using GPT
    const doc1Data = await parseDocument(openai, text1);
    const doc2Data = await parseDocument(openai, text2);

    // Compare estimates
    const comparison = await compareEstimates(openai, doc1Data, doc2Data);

    return NextResponse.json({ comparison });
  } catch (error) {
    console.error("Error processing comparison:", error);
    return NextResponse.json(
      { error: "Failed to process comparison" },
      { status: 500 }
    );
  }
}

async function parseDocument(openai: OpenAI, text: string) {
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful assistant that parses insurance estimates into structured data.",
      },
      {
        role: "user",
        content: `Parse the following insurance estimate into structured format:
        ${text}
        
        Return only a JSON object with this structure:
        {
          "line_items": [
            {
              "description": "",
              "cost": 0.0,
              "quantity": 0,
              "notes": ""
            }
          ],
          "total_cost": 0.0
        }`,
      },
    ],
    temperature: 0,
  });

  // Clean and parse the JSON response
  const jsonResponse = response.choices[0].message.content;
  const cleanedJson = jsonResponse.replace(/```json|```/g, "").trim();
  return JSON.parse(cleanedJson);
}

async function compareEstimates(openai: OpenAI, doc1Data: any, doc2Data: any) {
  const response = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful assistant that analyzes differences between insurance estimates.",
      },
      {
        role: "user",
        content: `Compare these insurance estimates and identify key differences:
        Estimate 1: ${JSON.stringify(doc1Data)}
        Estimate 2: ${JSON.stringify(doc2Data)}
        
        Return only a JSON object with this structure:
        {
          "numerical_differences": [
            {
              "item": "",
              "estimate1_value": "",
              "estimate2_value": "",
              "difference": ""
            }
          ],
          "scope_differences": [
            {
              "description": "",
              "explanation": ""
            }
          ],
          "total_cost_difference": 0.0,
          "summary": ""
        }`,
      },
    ],
    temperature: 0,
  });

  // Clean and parse the JSON response
  const jsonResponse = response.choices[0].message.content;
  const cleanedJson = jsonResponse.replace(/```json|```/g, "").trim();
  return JSON.parse(cleanedJson);
}
