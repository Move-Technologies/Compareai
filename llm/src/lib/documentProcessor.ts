import { pdf } from "pdf-parse";

interface LineItem {
  description: string;
  cost: number;
  quantity: number;
  lineNumber: number;
}
export class DocumentProcessor {
  // First, use regex and traditional parsing for initial data extraction
  private extractBasicData(text: string): LineItem[] {
    // Basic pattern matching for common insurance estimate formats
    const pattern = /(\d+)\.\s*(.*?)\s*\$?([\d,]+\.?\d*)\s*x?\s*(\d+)?/g;
    const items: LineItem[] = [];

    let match;
    while ((match = pattern.exec(text)) !== null) {
      items.push({
        lineNumber: parseInt(match[1]),
        description: match[2].trim(),
        cost: parseFloat(match[3].replace(/,/g, "")),
        quantity: match[4] ? parseInt(match[4]) : 1,
      });
    }

    return items;
  }

  // Then, use GPT only for comparing smaller chunks of relevant differences
  private async compareChunks(items1: LineItem[], items2: LineItem[]) {
    // Find obvious numerical differences first
    const numericalDiffs = this.findNumericalDifferences(items1, items2);

    // Only send ambiguous items to GPT
    const ambiguousItems = this.findAmbiguousItems(items1, items2);

    if (ambiguousItems.length > 0) {
      // Batch ambiguous items in smaller chunks
      const chunks = this.chunkArray(ambiguousItems, 5);
      const analyses = await Promise.all(
        chunks.map((chunk) => this.analyzeChunkWithGPT(chunk))
      );
      return { numericalDiffs, subjectiveDiffs: analyses.flat() };
    }

    return { numericalDiffs, subjectiveDiffs: [] };
  }

  private findNumericalDifferences(
    items1: LineItem[],
    items2: LineItem[]
  ): any[] {
    // Compare exact matches first
    return items1.reduce((diffs: any[], item1) => {
      const match = items2.find(
        (item2) =>
          item2.description.toLowerCase() === item1.description.toLowerCase()
      );

      if (
        match &&
        (match.cost !== item1.cost || match.quantity !== item1.quantity)
      ) {
        diffs.push({
          description: item1.description,
          diff: {
            cost: match.cost - item1.cost,
            quantity: match.quantity - item1.quantity,
          },
        });
      }
      return diffs;
    }, []);
  }

  private async analyzeChunkWithGPT(items: any[]) {
    // Only use GPT for complex comparisons
    const prompt = `Compare these potentially related insurance estimate items and identify if they refer to the same work with different terminology. Only identify genuine matches:
    Items: ${JSON.stringify(items, null, 2)}
    
    Return ONLY matches found in JSON format with explanation.`;

    const response = await openai.chat.completions.create({
      model: "gpt-3.5-turbo", // Using 3.5 for cost efficiency
      messages: [{ role: "user", content: prompt }],
      max_tokens: 150, // Limiting token usage
    });

    return JSON.parse(response.choices[0].message.content || "[]");
  }
}
