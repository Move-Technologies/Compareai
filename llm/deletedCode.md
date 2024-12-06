from comarison-tool

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
                      {/* <p className="text-2xl font-bold">{result.file1_count}</p> */}
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">
                        Items in Carrier's Estimate
                      </p>
                      {/* <p className="text-2xl font-bold">{result.file2_count}</p> */}
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">
                        Total Discrepancies
                      </p>
                      <p className="text-2xl font-bold">
                        {/* {result.overall_summary.total_discrepancies} */}
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
                        {/* " result.overall_summary.average_difference_percentage"
                        % */}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Insights */}
              {/* {renderAIInsights(result.ai_insights)} */}

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













            from appraiser0view

                 <Card>
        <CardHeader>
          <CardTitle>Market Rate Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-red-50 rounded-lg">
              <h3 className="text-sm font-medium text-red-800">
                High Variance Items
              </h3>
              <p className="text-2xl font-bold text-red-800">
             "   {/* {varianceGroups.highVariance.length}' */}"
              </p>
              <p className="text-sm text-red-600">Above 20% variance</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h3 className="text-sm font-medium text-yellow-800">
                Moderate Variance Items
              </h3>
              <p className="text-2xl font-bold text-yellow-800">
                "{/* {varianceGroups.moderateVariance.length} */}"
              </p>
              <p className="text-sm text-yellow-600">10-20% variance</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="text-sm font-medium text-green-800">
                Market-Aligned Items
              </h3>
              <p className="text-2xl font-bold text-green-800">
                "{/* {varianceGroups.lowVa"riance.length} */}"
              </p>
              <p className="text-sm text-green-600">Under 10% variance</p>
            </div>
          </div>

          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="high-variance">
              <AccordionTrigger>
                {/* High Variance Items ({varianceGroups.highVariance.length}) */}
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {/* {varianceGroups.highVariance.map((item, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-medium">{item.description}</h4>
                          <p className="text-sm text-gray-600">
                            Category: {item.category}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-red-600 font-medium">
                            {formatPercentage(item.percentage_difference)}%
                            variance
                          </p>
                          <p className="text-sm text-gray-600">
                            Carrier: {formatCurrency(item.doc2_cost)} vs Yours:{" "}
                            {formatCurrency(item.doc1_cost)}
                          </p>
                        </div>
                      </div>
                      {item.doc1_occurrences && (
                        <div className="text-sm text-gray-600">
                          <p>
                            Documentation Available:{" "}
                            {item.doc1_occurrences.occurrences_detail.length}{" "}
                            references
                          </p>
                        </div>
                      )}
                    </div>
                  ))} */}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>