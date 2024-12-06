import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const VarianceComparison = ({ data }: { data: any }) => {
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

    Object.values(data.categorized_items).forEach((category) => {
      (category.items || []).forEach((item) => {
        estimate1Total += item.doc1_cost || 0;
        estimate2Total += item.doc2_cost || 0;
      });
    });

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
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Category</th>
                <th className="text-right py-2">Your Estimate</th>
                <th className="text-right py-2">Other Estimate</th>
                <th className="text-right py-2">Difference</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.categorized_items).map(
                ([category, details]) => {
                  const categoryTotal1 = (details.items || []).reduce(
                    (sum, item) => sum + (item.doc1_cost || 0),
                    0
                  );
                  const categoryTotal2 = (details.items || []).reduce(
                    (sum, item) => sum + (item.doc2_cost || 0),
                    0
                  );
                  const variance = categoryTotal1 - categoryTotal2;

                  return (
                    <tr key={category} className="border-b">
                      <td className="py-2">{category}</td>
                      <td className="text-right py-2">
                        {formatCurrency(categoryTotal1)}
                      </td>
                      <td className="text-right py-2">
                        {formatCurrency(categoryTotal2)}
                      </td>
                      <td
                        className={`text-right py-2 ${
                          variance > 0
                            ? "text-red-600"
                            : variance < 0
                            ? "text-green-600"
                            : ""
                        }`}
                      >
                        {formatCurrency(variance)}
                      </td>
                    </tr>
                  );
                }
              )}
              <tr className="font-bold bg-gray-50">
                <td className="py-2">Items RCV Subtotal</td>
                <td className="text-right py-2">
                  {formatCurrency(totals.estimate1Total)}
                </td>
                <td className="text-right py-2">
                  {formatCurrency(totals.estimate2Total)}
                </td>
                <td
                  className={`text-right py-2 ${
                    totals.varianceTotal > 0 ? "text-red-600" : "text-green-600"
                  }`}
                >
                  {formatCurrency(totals.varianceTotal)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

export default VarianceComparison;
