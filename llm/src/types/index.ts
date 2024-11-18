// Basic types
export type Severity = "normal" | "high" | "critical";

// Single occurrence interface
interface Occurrence {
  line_number: number;
  op: number;
  quantity: number;
  rcv: number;
  tax: number;
  unit_cost: number;
  total_cost: number;
  unit: string;
}

// Occurrence summary interface
export interface OccurrenceSummary {
  total_quantity: number;
  total_rcv: number;
  occurrences_detail: string[];
}

// Line item interface
export interface LineItem {
  // Existing fields
  description: string;
  doc1_quantity: number;
  doc2_quantity: number;
  doc1_cost: number;
  doc2_cost: number;
  unit: string;
  cost_difference: number;
  percentage_difference: number;
  severity: Severity;
  is_labor: boolean;
  is_temporary: boolean;
  doc1_occurrences: OccurrenceSummary;
  doc2_occurrences: OccurrenceSummary | null;
  match_confidence: number;

  // Additional fields from all_items array
  quantity: number;
  unit_cost: number;
  tax: number;
  op: number;
  rcv: number;
  total_cost: number;
  occurrences: Array<{
    quantity: number;
    unit_cost: number;
    tax: number;
    op: number;
    rcv: number;
    line_number: number;
  }>;
  occurrence_count: number;
  occurrence_summary: {
    total_quantity: number;
    total_rcv: number;
    occurrences_detail: string[];
  };
}
// Summary statistics interface
export interface SummaryStats {
  total_items: number;
  total_cost_difference: string;
  average_cost_difference_percentage: string;
  categories: Record<string, number>;
  significant_differences: number;
  labor_vs_material_split: {
    labor_items: number;
    material_items: number;
  };
}

// Detailed analysis interfaces
export interface CategorySummary {
  total_items: number;
  total_doc1_cost: number;
  total_doc2_cost: number;
  total_difference: number;
  average_difference_percentage: number;
  critical_items: number;
  high_difference_items: number;
}

export interface CategoryAIInsight {
  reasons: string[];
  recommendations: string[];
  risk_assessment: string;
  impact_analysis: string;
}

export interface CategoryDetail {
  items: LineItem[];
  summary: CategorySummary;
}

export interface DetailedAnalysis {
  categorized_items: Record<string, CategoryDetail>;
  overall_summary: {
    total_categories: number;
    total_items: number;
    total_doc1_cost: number;
    total_doc2_cost: number;
    total_difference: number;
    average_difference_percentage: number;
    critical_items_count: number;
    high_difference_items_count: number;
    categories_by_impact: [string, number][];
  };
  ai_insights: Record<string, CategoryAIInsight>;
}

// Comparison results interface
export interface ComparisonResults {
  all_items: LineItem[];
  cost_discrepancies: LineItem[];
  quantity_discrepancies: LineItem[];
  unique_to_doc1: LineItem[];
  unique_to_doc2: LineItem[];
}

// Main API response interface
export interface APIResponse {
  status: "success" | "error";
  summary_stats: SummaryStats;
  detailed_analysis: DetailedAnalysis;
  comparison_results: ComparisonResults;
  error?: string;
}

export interface ComparisonResponse {
  status: "success" | "error";
  error?: string; // only present if status is 'error'
  detailed_analysis: {
    categorized_items: {
      [category: string]: {
        items: Array<{
          description: string;
          doc1_quantity: number;
          doc2_quantity: number;
          doc1_cost: number;
          doc2_cost: number;
          unit: string;
          cost_difference: number;
          percentage_difference: number;
          is_labor: boolean;
          is_temporary: boolean;
          doc1_occurrences: {
            total_quantity: number;
            total_rcv: number;
            occurrences_detail: string[];
          };
          doc2_occurrences: {
            total_quantity: number;
            total_rcv: number;
            occurrences_detail: string[];
          };
          match_confidence: number;
          quantity?: number;
          unit_cost?: number;
          tax?: number;
          op?: number;
          rcv?: number;
          total_cost?: number;
          occurrences?: any[];
          occurrence_count?: number;
          occurrence_summary?: {
            total_quantity: number;
            total_rcv: number;
            occurrences_detail: string[];
          };
        }>;
        summary: {
          total_items: number;
          total_cost_difference: number;
          average_cost_difference: number;
          items_with_discrepancies: number;
        };
      };
    };
    overall_summary: {
      total_items: number;
      total_discrepancies: number;
      total_cost_difference: number;
      average_difference_percentage: number;
      categories_affected: number;
    };
    ai_insights: AIInsights;
  };
  comparison_results: {
    all_items: Array<{
      description: string;
      doc1_quantity: number;
      doc1_cost: number;
      unit: string;
      doc1_occurrences: {
        total_quantity: number;
        total_rcv: number;
        occurrences_detail: string[];
      };
      doc2_quantity: number | null;
      doc2_cost: number | null;
      doc2_occurrences: {
        total_quantity: number;
        total_rcv: number;
        occurrences_detail: string[];
      } | null;
      quantity_difference: number | null;
      cost_difference: number | null;
      percentage_cost_difference: number | null;
      match_confidence: number;
    }>;
    cost_discrepancies: Array<{
      description: string;
      doc1_cost: number;
      doc2_cost: number;
      difference: number;
      match_confidence: number;
    }>;
    quantity_discrepancies: Array<{
      description: string;
      doc1_quantity: number;
      doc2_quantity: number;
      difference: number;
      match_confidence: number;
    }>;
    unique_to_doc1: Array<Record<string, any>>; // Items only found in first document
    unique_to_doc2: Array<Record<string, any>>; // Items only found in second document
  };
}

export interface AIInsights {
  summary?: {
    total_underpaid_amount: number;
    number_of_underpaid_items: number;
    largest_discrepancies: Array<{
      description: string;
      doc1_cost: number;
      doc2_cost: number;
      cost_difference: number;
      percentage_cost_difference: number;
      category: string;
    }>;
  };
  key_findings?: string[];
  recommendations?: Array<{
    priority: "High" | "Medium" | "Low";
    action: string;
    details: string[];
  }>;
  negotiation_strategy?: {
    primary_focus: string;
    documentation_needed: string[];
    talking_points: string[];
    common_carrier_positions: string[];
  };
  potential_recoverable_amount?: {
    total_potential: number;
    breakdown: {
      highly_likely: number;
      moderately_likely: number;
      requires_additional_documentation: number;
    };
    next_steps: string[];
  };
}

// Export all interfaces
export type { Occurrence };
