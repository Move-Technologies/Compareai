import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
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

const VarianceComparison = ({ data }: { data: any }) => {
  const dataRows = data?.recap_comparison?.comparison_results || [];
  const [currentPage, setCurrentPage] = useState(3);

  const paginatedData = dataRows.slice(
    currentPage * ITEMS_PER_PAGE,
    (currentPage + 1) * ITEMS_PER_PAGE
  );
  console.log(paginatedData);

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
                <TableHead className="" colSpan={1}>
                  Category
                </TableHead>
                <TableHead className="text-center">Your Estimate</TableHead>
                <TableHead className="text-center">Other Estimate</TableHead>
                <TableHead className="text-right">Difference</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.map((row, idx) => (
                <TableRow key={`row-recap-${idx}`} className="border-b">
                  <TableCell className="py-2" colSpan={1}>
                    {row.category}
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
          <Pagination
            currentPage={currentPage}
            numberOfRows={dataRows.length}
            setCurrentPage={setCurrentPage}
          />
        </div>
      </CardContent>
    </Card>
  );
};

function Pagination({
  setCurrentPage,
  currentPage,
  numberOfRows,
}: {
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>;
  currentPage: number;
  numberOfRows: number;
}) {
  const numberOfPages = Math.ceil(numberOfRows / ITEMS_PER_PAGE);
  if (numberOfPages <= 1) return;

  return (
    <div className="flex justify-center mx-auto w-fit mt-4  border border-gray-300 rounded-sm">
      {Array.from({ length: numberOfPages }).map((_, index) => (
        <span
          key={index}
          className={cn(
            `cursor-pointer  duration-200 text-primary py-0.5 px-2 border-l first:border-l-0 hover:bg-muted rounded-sm`,
            {
              "bg-muted": index === currentPage,
            }
          )}
          onClick={() => setCurrentPage(index)}
        >
          {index + 1}
        </span>
      ))}
    </div>
  );
}

export default VarianceComparison;
