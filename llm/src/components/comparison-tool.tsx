"use client";
import { useState, useEffect } from "react";
import { Upload, FileText, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { put } from "@vercel/blob";
import {
  AIInsights,
  ComparisonResponse,
  type APIResponse,
  type LineItem,
} from "@/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import AppraiserView from "./appraiser-view";

const safeNumber = (value: any): number => {
  if (value === null || value === undefined) return 0;
  const num = Number(value);
  return isNaN(num) ? 0 : num;
};

const formatCurrency = (value: any): string => {
  if (value === null || value === undefined) return "$0.00";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

const formatPercentage = (value: any): string => {
  if (value === null || value === undefined) return "0.0";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "0.0";
  return num.toFixed(1);
};

const formatQuantity = (value: any): string => {
  if (value === null || value === undefined) return "0";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "0";
  return Number.isInteger(num) ? num.toString() : num.toFixed(2);
};

const combineRedundantItems = (items: any[]) => {
  if (!items || !Array.isArray(items)) return [];

  // Helper function to extract and sum values from occurrence details
  const calculateTotalsFromDetails = (details: string[]) => {
    let totalQuantity = 0;
    let totalRcv = 0;

    details.forEach((detail) => {
      // Extract quantity and RCV from detail string
      // Format example: "Line 1 (Page 1): Qty=2, RCV=$100.00"
      const qtyMatch = detail.match(/Qty=(\d*\.?\d*)/);
      const rcvMatch = detail.match(/RCV=\$(\d*\.?\d*)/);

      if (qtyMatch && qtyMatch[1]) {
        totalQuantity += parseFloat(qtyMatch[1]);
      }
      if (rcvMatch && rcvMatch[1]) {
        totalRcv += parseFloat(rcvMatch[1]);
      }
    });

    return { totalQuantity, totalRcv };
  };

  // First, normalize all descriptions to avoid case/spacing mismatches
  const combinedItems = items.reduce((acc, item) => {
    // Use description as the key for matching similar items
    const key = item.description?.toLowerCase().trim();
    if (!key) return acc;

    if (!acc[key]) {
      // First occurrence of this item
      const doc1Details = item.doc1_occurrences?.occurrences_detail || [];
      const doc2Details = item.doc2_occurrences?.occurrences_detail || [];

      // Calculate totals from occurrence details
      const doc1Totals = calculateTotalsFromDetails(doc1Details);
      const doc2Totals = calculateTotalsFromDetails(doc2Details);

      acc[key] = {
        ...item,
        doc1_occurrences: {
          occurrences_detail: new Set(doc1Details),
          total_quantity: doc1Totals.totalQuantity,
          total_rcv: doc1Totals.totalRcv,
        },
        doc2_occurrences: {
          occurrences_detail: new Set(doc2Details),
          total_quantity: doc2Totals.totalQuantity,
          total_rcv: doc2Totals.totalRcv,
        },
      };
    } else {
      // Found another occurrence of the same item
      if (item.doc1_occurrences?.occurrences_detail) {
        item.doc1_occurrences.occurrences_detail.forEach((detail: string) => {
          acc[key].doc1_occurrences.occurrences_detail.add(detail);
        });
      }

      if (item.doc2_occurrences?.occurrences_detail) {
        item.doc2_occurrences.occurrences_detail.forEach((detail: string) => {
          acc[key].doc2_occurrences.occurrences_detail.add(detail);
        });
      }

      // Recalculate totals after adding new occurrences
      const doc1Totals = calculateTotalsFromDetails(
        Array.from(acc[key].doc1_occurrences.occurrences_detail)
      );
      const doc2Totals = calculateTotalsFromDetails(
        Array.from(acc[key].doc2_occurrences.occurrences_detail)
      );

      // Update totals
      acc[key].doc1_occurrences.total_quantity = doc1Totals.totalQuantity;
      acc[key].doc1_occurrences.total_rcv = doc1Totals.totalRcv;
      acc[key].doc2_occurrences.total_quantity = doc2Totals.totalQuantity;
      acc[key].doc2_occurrences.total_rcv = doc2Totals.totalRcv;
    }
    return acc;
  }, {});

  // Convert back to array and convert Sets back to arrays
  return Object.values(combinedItems).map((item) => ({
    ...item,
    doc1_occurrences: {
      ...item.doc1_occurrences,
      occurrences_detail: Array.from(item.doc1_occurrences.occurrences_detail),
    },
    doc2_occurrences: {
      ...item.doc2_occurrences,
      occurrences_detail: Array.from(item.doc2_occurrences.occurrences_detail),
    },
  }));
};

const adjustPageNumbers = (occurrences: any) => {
  if (!occurrences?.occurrences_detail) return occurrences;

  return {
    ...occurrences,
    occurrences_detail: occurrences.occurrences_detail.map((detail: string) => {
      // Find page number in the detail string and increment it
      return detail.replace(/Page (\d+)/i, (match, pageNum) => {
        return `Page ${parseInt(pageNum) + 1}`;
      });
    }),
  };
};

const ComparisonApp = () => {
  const [files, setFiles] = useState({ file1: null, file2: null });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState(
    "Analyzing your documents..."
  );

  const loadingMessages = [
    "Analyzing your documents...",
    "Comparing line items...",
    "Crunching the numbers...",
    "Almost there...",
    "Our AI is working its magic...",
    "Generating insights...",
  ];

  useEffect(() => {
    if (!loading) return;

    const interval = setInterval(() => {
      setLoadingMessage((prev) => {
        const currentIndex = loadingMessages.indexOf(prev);
        const nextIndex = (currentIndex + 1) % loadingMessages.length;
        return loadingMessages[nextIndex];
      });
    }, 10000);

    return () => clearInterval(interval);
  }, [loading]);

  const handleFileChange = (e, fileNum) => {
    const file = e.target.files[0];
    if (file && file.type === "application/pdf") {
      setFiles((prev) => ({ ...prev, [fileNum]: file }));
      setError(null);
    } else {
      setError("Please upload PDF files only");
    }
  };

  const handleSubmit = async () => {
    if (!files.file1 || !files.file2) {
      setError("Please upload both files");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // const uploadPromises = await Promise.all([
      //   put(`estimates/${Date.now()}-${files.file1.name}`, files.file1, {
      //     access: "public",
      //     token:
      //       "vercel_blob_rw_9ylyweWN5g4q973s_CWIJJrVXOesAKMWGnela0arrEmre2R",
      //   }),
      //   put(`estimates/${Date.now()}-${files.file2.name}`, files.file2, {
      //     access: "public",
      //     token:
      //       "vercel_blob_rw_9ylyweWN5g4q973s_CWIJJrVXOesAKMWGnela0arrEmre2R",
      //   }),
      // ]);

      // const [blob1, blob2] = uploadPromises;

      // Proceed with original file processing
      const formData = new FormData();
      formData.append("file1", files.file1);
      formData.append("file2", files.file2);

      const response = await fetch(
        "https://api.getgrunt.co/api/compare",
        // "http://localhost:5000/api/compare",
        // "https://flask-hello-world-lake-nu.vercel.app/api/compare",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Failed to compare files");
      }

      const rawData = await response.text(); // Get raw response text first

      // Replace NaN with null in the raw JSON string
      const sanitizedData = rawData.replace(/:\s*NaN/g, ": null");

      try {
        // Parse the sanitized JSON
        const data = JSON.parse(sanitizedData);

        // Additional sanitization of parsed data
        const sanitizeValue = (value: any) => {
          if (value === null || value === undefined || Number.isNaN(value)) {
            return 0;
          }
          return value;
        };

        const sanitizeObject = (obj: any): APIResponse => {
          if (!obj || typeof obj !== "object") return obj;

          const newObj: any = Array.isArray(obj) ? [] : {};

          for (const key in obj) {
            if (typeof obj[key] === "object" && obj[key] !== null) {
              newObj[key] = sanitizeObject(obj[key]);
            } else if (typeof obj[key] === "number") {
              newObj[key] = sanitizeValue(obj[key]);
            } else {
              newObj[key] = obj[key];
            }
          }

          return newObj as APIResponse;
        };

        const sanitizedResult = sanitizeObject(data);
        setResult(sanitizedResult);
      } catch (parseError) {
        console.error("JSON Parse Error:", parseError);
        console.log("Raw response:", rawData);
        throw new Error("Failed to parse comparison results");
      }
    } catch (err) {
      setError(err.message);
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  console.log(result);

  const renderLineItem = (item: any) => {
    if (!item) return null;

    // Adjust page numbers in occurrences
    const adjustedItem = {
      ...item,
      doc1_occurrences: adjustPageNumbers(item.doc1_occurrences),
      doc2_occurrences: adjustPageNumbers(item.doc2_occurrences),
    };

    // Safe access helper function
    const safe = (value: any, defaultValue: any = 0) => {
      return value !== undefined && value !== null ? value : defaultValue;
    };

    return (
      <div key={item.description || "unnamed-item"} className="border-t py-4">
        <div className="space-y-3">
          {/* Header with description and match confidence */}
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-lg">
              {item.description || "Unnamed Item"}
            </h4>
            {/* <span className="text-sm text-gray-600">
              Match Confidence: {formatPercentage(safe(item.match_confidence))}%
            </span> */}
          </div>

          {/* Main comparison grid */}
          <div className="grid grid-cols-2 gap-8">
            {/* Your Estimate */}
            <div>
              <p className="text-sm font-medium text-gray-600">Your Estimate</p>
              <p className="text-xl font-semibold">
                {formatCurrency(safe(item.doc1_occurrences?.total_rcv))}
              </p>
              {item.doc1_occurrences?.total_quantity && (
                <p className="text-sm text-gray-600">
                  Quantity:{" "}
                  {formatQuantity(safe(item.doc1_occurrences.total_quantity))}{" "}
                  {item.unit || "EA"}
                </p>
              )}

              {/* Doc1 Occurrences */}
              {item.doc1_occurrences && (
                <div className="mt-2">
                  <Accordion type="single" collapsible>
                    <AccordionItem value="doc1-occurrences">
                      <AccordionTrigger className="text-sm">
                        Line Occurrences (
                        {
                          (item.doc1_occurrences.occurrences_detail || [])
                            .length
                        }
                        )
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-3">
                          {(item.doc1_occurrences.occurrences_detail || []).map(
                            (detail: string, idx: number) => (
                              <p key={idx} className="text-sm text-gray-600">
                                {detail}
                              </p>
                            )
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              )}
            </div>

            {/* Carrier Estimate */}
            <div>
              <p className="text-sm font-medium text-gray-600">
                Carrier Estimate
              </p>
              <p className="text-xl font-semibold">
                {formatCurrency(safe(item.doc2_occurrences.total_rcv))}
              </p>
              {item.doc2_occurrences?.total_quantity && (
                <p className="text-sm text-gray-600">
                  Quantity:{" "}
                  {formatQuantity(safe(item.doc2_occurrences.total_quantity))}{" "}
                  {item.unit || "EA"}
                </p>
              )}

              {/* Doc2 Occurrences */}
              {item.doc2_occurrences && (
                <div className="mt-2">
                  <Accordion type="single" collapsible>
                    <AccordionItem value="doc2-occurrences">
                      <AccordionTrigger className="text-sm">
                        Line Occurrences (
                        {
                          (item.doc2_occurrences.occurrences_detail || [])
                            .length
                        }
                        )
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-3">
                          {(item.doc2_occurrences.occurrences_detail || []).map(
                            (detail: string, idx: number) => (
                              <p key={idx} className="text-sm text-gray-600">
                                {detail}
                              </p>
                            )
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              )}
            </div>
          </div>

          {/* Differences Section */}
          <div className="mt-4 space-y-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p>
                  Cost Difference:{" "}
                  {formatCurrency(
                    safe(item.cost_difference || item.difference)
                  )}
                </p>
                {item.percentage_difference && (
                  <p>
                    Percentage Difference:{" "}
                    {formatPercentage(safe(item.percentage_difference))}%
                  </p>
                )}
              </div>
              {item.quantity_difference !== undefined && (
                <div>
                  <p>
                    Quantity Difference:{" "}
                    {formatQuantity(safe(item.quantity_difference))}{" "}
                    {item.unit || "EA"}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Tags */}
          <div className="flex gap-2">
            {item.is_labor && (
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                Labor
              </span>
            )}
            {item.is_temporary && (
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                Temporary
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Add new components for AI Insights
  const renderAIInsights = (insights: AIInsights) => {
    if (!insights) return null;

    return (
      <div className="space-y-6">
        {/* Summary Card */}
        {/* {insights.summary && (
          <Card>
            <CardHeader>
              <CardTitle>AI Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <p className="text-sm text-gray-500">
                    Total Underpaid Amount
                  </p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(insights.summary.total_underpaid_amount)}
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-500">Underpaid Items</p>
                  <p className="text-2xl font-bold">
                    {insights.summary.number_of_underpaid_items}
                  </p>
                </div>
                {insights.potential_recoverable_amount && (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-500">Potential Recovery</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(
                        insights.potential_recoverable_amount.total_potential
                      )}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )} */}

        {/* Largest Discrepancies */}
        {/* {insights.summary?.largest_discrepancies?.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Largest Discrepancies</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {insights.summary.largest_discrepancies.map((item, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{item.description}</p>
                        <p className="text-sm text-gray-600">
                          Category: {item.category}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-red-600 font-medium">
                          {formatCurrency(item.cost_difference)}
                        </p>
                        <p className="text-sm text-gray-600">
                          ({formatPercentage(item.percentage_cost_difference)}%
                          difference)
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )} */}

        {/* Key Findings and Recommendations Grid */}
        {(insights.key_findings?.length > 0 ||
          insights.recommendations?.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Key Findings */}
            {insights.key_findings?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Key Findings</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {insights.key_findings
                      .filter(
                        (finding) =>
                          !finding.toLowerCase().includes("missing items")
                      )
                      .map((finding, index) => (
                        <li key={index} className="flex gap-2">
                          <span className="text-blue-500">•</span>
                          <span className="text-sm">{finding}</span>
                        </li>
                      ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Recommendations */}
            {insights.recommendations?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {insights.recommendations.map((rec, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs ${
                              rec.priority === "High"
                                ? "bg-red-100 text-red-800"
                                : rec.priority === "Medium"
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-green-100 text-green-800"
                            }`}
                          >
                            {rec.priority} Priority
                          </span>
                          <p className="font-medium">{rec.action}</p>
                        </div>
                        <ul className="ml-4 space-y-1">
                          {rec.details.map((detail, idx) => (
                            <li key={idx} className="text-sm text-gray-600">
                              • {detail}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Negotiation Strategy */}
        {insights.negotiation_strategy && (
          <Card>
            <CardHeader>
              <CardTitle>Negotiation Strategy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Primary Focus */}
                <div>
                  <h4 className="font-medium mb-2">Primary Focus</h4>
                  <p className="text-sm text-gray-600">
                    {insights.negotiation_strategy.primary_focus}
                  </p>
                </div>

                {/* Documentation Needed */}
                {insights.negotiation_strategy.documentation_needed?.length >
                  0 && (
                  <div>
                    <h4 className="font-medium mb-2">Required Documentation</h4>
                    <ul className="space-y-1">
                      {insights.negotiation_strategy.documentation_needed.map(
                        (doc, index) => (
                          <li key={index} className="text-sm text-gray-600">
                            • {doc}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {/* Talking Points */}
                {insights.negotiation_strategy.talking_points?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Key Talking Points</h4>
                    <ul className="space-y-1">
                      {insights.negotiation_strategy.talking_points.map(
                        (point, index) => (
                          <li key={index} className="text-sm text-gray-600">
                            • {point}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {/* Carrier Positions */}
                {insights.negotiation_strategy.common_carrier_positions
                  ?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">
                      Anticipated Carrier Positions
                    </h4>
                    <ul className="space-y-1">
                      {insights.negotiation_strategy.common_carrier_positions.map(
                        (position, index) => (
                          <li key={index} className="text-sm text-gray-600">
                            • {position}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recovery Potential */}
        {insights.potential_recoverable_amount.amount !== 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recovery Potential</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Amount Breakdown */}
                {insights.potential_recoverable_amount.breakdown && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-gray-600">Highly Likely</p>
                      <p className="text-xl font-bold text-green-600">
                        {formatCurrency(
                          insights.potential_recoverable_amount.breakdown
                            ?.highly_likely ?? 0
                        )}
                      </p>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <p className="text-sm text-gray-600">Moderately Likely</p>
                      <p className="text-xl font-bold text-yellow-600">
                        {formatCurrency(
                          insights.potential_recoverable_amount.breakdown
                            ?.moderately_likely ?? 0
                        )}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        Requires Documentation
                      </p>
                      <p className="text-xl font-bold text-gray-600">
                        {formatCurrency(
                          insights.potential_recoverable_amount.breakdown
                            ?.requires_additional_documentation ?? 0
                        )}
                      </p>
                    </div>
                  </div>
                )}

                {/* Next Steps */}
                {insights.potential_recoverable_amount.next_steps?.length >
                  0 && (
                  <div>
                    <h4 className="font-medium mb-2">Recommended Next Steps</h4>
                    <ul className="space-y-1">
                      {insights.potential_recoverable_amount.next_steps.map(
                        (step, index) => (
                          <li key={index} className="text-sm text-gray-600">
                            • {step}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderUniqueItem = (item: LineItem) => {
    return (
      <div key={item.description} className="border-t py-4">
        <div className="space-y-3">
          {/* Header with description */}
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-lg">{item.description}</h4>
          </div>

          {/* Your Estimate */}
          <div>
            <p className="text-sm font-medium text-gray-600">Your Estimate</p>
            <p className="text-xl font-semibold">{formatCurrency(item.rcv)}</p>
            <p className="text-sm text-gray-600">
              Quantity: {formatQuantity(item.quantity)} {item.unit}
            </p>

            {/* Line Occurrences (if they exist) */}
            {item.doc1_occurrences && (
              <div className="mt-2">
                <Accordion type="single" collapsible>
                  <AccordionItem value="occurrences">
                    <AccordionTrigger className="text-sm">
                      Line Occurrences
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-2">
                        {item.doc1_occurrences.occurrences_detail.map(
                          (detail, idx) => (
                            <p key={idx} className="text-sm text-gray-600">
                              {detail}
                            </p>
                          )
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">
          Insurance Estimate Comparison
        </h1>
        <p className="text-gray-600">
          Upload two insurance estimate PDFs to compare them
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {["file1", "file2"].map((fileKey) => (
          <div key={fileKey} className="border rounded-lg p-4">
            <div className="flex items-center mb-4">
              <FileText className="mr-2" />
              <h2 className="text-lg font-semibold">
                {fileKey === "file1" ? "Your Estimate" : "Carrier's Estimate"}
              </h2>
            </div>

            <div className="relative">
              <input
                type="file"
                onChange={(e) => handleFileChange(e, fileKey)}
                accept=".pdf"
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100"
              />
              {files[fileKey] && (
                <p className="mt-2 text-sm text-gray-600">
                  {files[fileKey].name}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || !files.file1 || !files.file2}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg
          hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
          flex items-center justify-center"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
        ) : (
          <>
            <Upload className="mr-2" size={20} />
            Compare Estimates
          </>
        )}
      </button>

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-lg text-center space-y-4 w-[400px] h-[200px] flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="text-lg font-medium animate-pulse w-[300px]">
              {loadingMessage}
            </p>
          </div>
        </div>
      )}
      {/* here are the tabs */}
      {result && (
        <div className="mt-8 space-y-6">
          <Tabs defaultValue="appraiser" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="appraiser">Recap</TabsTrigger>
              <TabsTrigger value="categories">Categories</TabsTrigger>
              <TabsTrigger value="discrepancies">Discrepancies</TabsTrigger>
              <TabsTrigger value="unique">Unique Items</TabsTrigger>
            </TabsList>

            {/* Appraiser View Tab */}
            <TabsContent value="appraiser">
              <AppraiserView data={result} />
            </TabsContent>

            {/* Other Views - Wrapped in a separate TabsContent */}
            <TabsContent value="categories">
              {/* Overall Summary Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Overall Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">
                        Items in Your Estimate
                      </p>
                      <p className="text-2xl font-bold">{result.file1_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">
                        Items in Carrier's Estimate
                      </p>
                      <p className="text-2xl font-bold">{result.file2_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">
                        Total Discrepancies
                      </p>
                      <p className="text-2xl font-bold">
                        {/* {result.overall_summary.total_discrepancies} */}
                        "result.overall_summary.total_discrepancies"
                      </p>
                    </div>
                    {/* <div>
                      <p className="text-sm text-gray-500">Cost Difference</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(
                          result.overall_summary.total_cost_difference
                        )}
                      </p>
                    </div> */}
                    <div>
                      <p className="text-sm text-gray-500">
                        Average Difference
                      </p>
                      <p className="text-2xl font-bold">
                        {/* {formatPercentage(
                          result.overall_summary.average_difference_percentage
                        )} */}
                        " result.overall_summary.average_difference_percentage"
                        %
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Insights */}
              {renderAIInsights(result.ai_insights)}

              {/* Categories Content */}
              <Accordion type="single" collapsible className="w-full">
                This is accordidion
              </Accordion>
            </TabsContent>

            {/* Discrepancies Tab */}
            <TabsContent value="discrepancies">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Cost Discrepancies</CardTitle>
                  </CardHeader>
                  <CardContent>
                    "{" "}
                    {/* " {result.comparison_results.cost_discrepancies.map(
                      renderLineItem
                    )}"" */}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Quantity Discrepancies</CardTitle>
                  </CardHeader>
                  <CardContent>
                    "{" "}
                    {/* {result.comparison_results.quantity_discrepancies.map(
                      renderLineItem
                    )} */}
                    "
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Unique Items Tab */}
            <TabsContent value="unique">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Items Unique to Your Estimate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    "
                    {/* {result.comparison_results.unique_to_doc1.map(
                      renderUniqueItem
                    )} */}
                    "
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Items Unique to Carrier's Estimate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    "{" "}
                    {/* " {result.comparison_results.unique_to_doc2.map(
                      renderUniqueItem
                    )}" */}
                    "
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
};
export default ComparisonApp;
