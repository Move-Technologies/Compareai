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
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";

const ITEMS_PER_PAGE = 10;

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

const VarianceComparison = ({
  data,
  titleComparison,
}: {
  data: any;
  titleComparison: string;
}) => {
  const objectToCompare = titleComparison.toLowerCase();
  const dataRows = data?.comparison_results || [];
  const [showMore, setShowMore] = React.useState(false);
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

  function handleShowMore() {
    setShowMore(!showMore);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Comparison Recap</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={cn("relative w-full overflow-x-auto overflow-y-hidden", {
            // "h-[300px]": !showMore,
          })}
        >
          <Table className="w-[600px] relative">
            <TableHeader>
              <TableRow>
                <TableHead className="" colSpan={1}>
                  {titleComparison}
                </TableHead>
                <TableHead className="text-center">Your Estimate</TableHead>
                <TableHead className="text-center">Other Estimate</TableHead>
                <TableHead className="text-right">Difference</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dataRows.map((row, idx) => (
                <TableRow key={`row-recap-${idx}`} className="border-b">
                  <TableCell className="py-2" colSpan={1}>
                    {row[objectToCompare]}
                  </TableCell>
                  <TableCell className="text-center py-2">
                    {row.your_estimate !== "N/A"
                      ? formatCurrency(row.your_estimate?.toFixed(2))
                      : "-"}
                  </TableCell>
                  <TableCell className="text-center py-2">
                    {row.carrier_estimate !== "N/A"
                      ? formatCurrency(row.carrier_estimate?.toFixed(2))
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
                      ? formatCurrency(row.difference?.toFixed(2))
                      : row.difference}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {/* {!showMore && (
            <>
              <div className="absolute w-full h-1/2 bottom-0 flex flex-col items-center">
                <Button
                  className="w-fit mt-10 absolute z-10"
                  onClick={handleShowMore}
                >
                  Show more
                </Button>
              </div>
              <div className="h-full w-full pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent to-gray-50"></div>
            </>
          )} */}
        </div>
      </CardContent>
    </Card>
  );
};

export default VarianceComparison;
