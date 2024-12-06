import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

const VarianceComparison = ({ data }: { data: any }) => {
  const dataRows = data?.recap_comparison?.comparison_results || [];
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return "$0.00";
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(num)) return "$0.00";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(num);
  };

  // Calculate totals
  const calculateTotals = () => {
    let estimate1Total = 0;
    let estimate2Total = 0;

    // Object.values(data.categorized_items).forEach((category) => {
    //   (category.items || []).forEach((item) => {
    //     estimate1Total += item.doc1_cost || 0;
    //     estimate2Total += item.doc2_cost || 0;
    //   });
    // });

    return {
      estimate1Total,
      estimate2Total,
      varianceTotal: estimate1Total - estimate2Total,
    };
  };

  const totals = calculateTotals();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Comparison Recap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative w-full overflow-x-auto">
          <Table className="w-[600px] relative">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Category</TableHead>
                <TableHead>Your Estimate</TableHead>
                <TableHead>Other Estimate</TableHead>
                <TableHead className="text-right">Difference</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dataRows.map((row, idx) => (
                <TableRow key={`row-recap-${idx}`} className="border-b">
                  <TableCell className="py-2">{row.category}</TableCell>
                  <TableCell className="text-center py-2">
                    {row.your_estimate !== "N/A"
                      ? row.your_estimate?.toFixed(2)
                      : "-"}
                  </TableCell>
                  <TableCell className="text-center py-2">
                    {row.carrier_estimate !== "N/A"
                      ? row.carrier_estimate?.toFixed(2)
                      : "-"}
                  </TableCell>
                  <TableCell
                    className={`text-right py-2 ${
                      row.difference > 0
                        ? "text-red-600"
                        : row.difference < 0
                        ? "text-green-600"
                        : ""
                    }`}
                  >
                    {row.difference !== "N/A"
                      ? row.difference?.toFixed(2)
                      : row.difference}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default VarianceComparison;
