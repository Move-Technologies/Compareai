import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import VarianceComparison from "./variance-view";

const AppraiserView = ({ data }: { data: any }) => {
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

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return "0.0";
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(num)) return "0.0";
    return num.toFixed(1);
  };

  // Group items by their pricing variance percentage
  const getPricingVarianceGroups = () => {
    const allItems = [];
    // const allItems = Object.values(data.categorized_items)
    //   .flatMap((category) => category.items || [])
    //   .filter((item) => item.percentage_difference !== undefined);

    // return {
    //   highVariance: allItems.filter(
    //     (item) => Math.abs(item.percentage_difference) > 20
    //   ),
    //   moderateVariance: allItems.filter(
    //     (item) =>
    //       Math.abs(item.percentage_difference) <= 20 &&
    //       Math.abs(item.percentage_difference) > 10
    //   ),
    //   lowVariance: allItems.filter(
    //     (item) => Math.abs(item.percentage_difference) <= 10
    //   ),
    // };
  };

  // const varianceGroups = getPricingVarianceGroups();

  return (
    <div className="space-y-6">
      {/* Market Rate Analysis */}
      {/* card must be here */}
      <VarianceComparison data={data} />
      {/* Labor vs Materials Analysis */}
      {/* <Card>
        <CardHeader>
          <CardTitle>Labor vs Materials Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Labor Analysis */}
      {/* <div>
              <h3 className="text-lg font-medium mb-4">Labor Costs</h3>
              {Object.entries(data.categorized_items).map(
                ([category, details]) => {
                  const laborItems =
                    details.items?.filter((item) => item.is_labor) || [];
                  if (laborItems.length === 0) return null;

                  return (
                    <div key={category} className="mb-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">
                        {category}
                      </h4>
                      {laborItems.map((item, index) => (
                        <div key={index} className="text-sm mb-2">
                          <div className="flex justify-between">
                            <span>{item.description}</span>
                            <span
                              className={
                                item.percentage_difference > 10
                                  ? "text-red-600"
                                  : "text-gray-600"
                              }
                            >
                              {formatPercentage(item.percentage_difference)}%
                              variance
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                }
              )}
            </div> */}

      {/* Materials Analysis */}
      {/* <div>
              <h3 className="text-lg font-medium mb-4">Material Costs</h3>
              {Object.entries(data.categorized_items).map(
                ([category, details]) => {
                  const materialItems =
                    details.items?.filter((item) => !item.is_labor) || [];
                  if (materialItems.length === 0) return null;

                  return (
                    <div key={category} className="mb-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">
                        {category}
                      </h4>
                      {materialItems.map((item, index) => (
                        <div key={index} className="text-sm mb-2">
                          <div className="flex justify-between">
                            <span>{item.description}</span>
                            <span
                              className={
                                item.percentage_difference > 10
                                  ? "text-red-600"
                                  : "text-gray-600"
                              }
                            >
                              {formatPercentage(item.percentage_difference)}%
                              variance
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                }
              )}
            </div>
          </div>
        </CardContent> 
      </Card> */}

      {/* Documentation Strength */}
      {/* <Card>
        <CardHeader>
          <CardTitle>Documentation Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(data.categorized_items).map(
              ([category, details]) => {
                const itemsWithDocs =
                  details.items?.filter(
                    (item) =>
                      item.doc1_occurrences?.occurrences_detail?.length > 0
                  ) || [];

                if (itemsWithDocs.length === 0) return null;

                return (
                  <div key={category}>
                    <h3 className="text-lg font-medium mb-3">{category}</h3>
                    {itemsWithDocs.map((item, index) => (
                      <div
                        key={index}
                        className="mb-4 p-4 bg-gray-50 rounded-lg"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-medium">{item.description}</h4>
                            <p className="text-sm text-gray-600">
                              {item.doc1_occurrences.occurrences_detail.length}{" "}
                              supporting references
                            </p>
                          </div>
                          <div className="text-right">
                            <p
                              className={`font-medium ${
                                item.percentage_difference > 10
                                  ? "text-red-600"
                                  : "text-green-600"
                              }`}
                            >
                              {formatPercentage(item.percentage_difference)}%
                              variance
                            </p>
                          </div>
                        </div>
                        <Accordion type="single" collapsible>
                          <AccordionItem value="details">
                            <AccordionTrigger className="text-sm">
                              View References
                            </AccordionTrigger>
                            <AccordionContent>
                              <ul className="space-y-2">
                                {item.doc1_occurrences.occurrences_detail.map(
                                  (detail, idx) => (
                                    <li
                                      key={idx}
                                      className="text-sm text-gray-600"
                                    >
                                      • {detail}
                                    </li>
                                  )
                                )}
                              </ul>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </div>
                    ))}
                  </div>
                );
              }
            )}
          </div>
        </CardContent>
      </Card> */}
    </div>
  );
};

export default AppraiserView;
