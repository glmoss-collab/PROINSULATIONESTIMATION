"""
API Usage and Cost Tracking
============================

Track token usage and costs across all API calls.
Helps monitor and optimize API spending.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# USAGE TRACKER
# ============================================================================

@dataclass
class APIUsageTracker:
    """
    Track API token usage and calculate costs.

    Supports Claude Opus 4.5 pricing with prompt caching.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    # Operation tracking
    operations: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    # Pricing constants (Claude Opus 4.5 - as of 2025)
    PRICE_INPUT_PER_MTK = 3.00  # Per million tokens
    PRICE_OUTPUT_PER_MTK = 15.00
    PRICE_CACHE_READ_PER_MTK = 0.30  # 90% cheaper than input
    PRICE_CACHE_WRITE_PER_MTK = 3.75  # 25% more than input

    def record_usage(self, response, operation: str = "api_call") -> None:
        """
        Record usage from Anthropic API response.

        Args:
            response: Anthropic Messages API response object
            operation: Name of the operation (for tracking)
        """
        usage = response.usage

        # Standard tokens
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens

        # Cache tokens (if available)
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)
        cache_write = getattr(usage, 'cache_creation_input_tokens', 0)

        # Update totals
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cache_read_tokens += cache_read
        self.cache_write_tokens += cache_write

        # Record individual operation
        self.operations.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read,
            "cache_write_tokens": cache_write,
            "cost_usd": self._calculate_operation_cost(
                input_tokens, output_tokens, cache_read, cache_write
            )
        })

        # Log if using cache
        if cache_read > 0:
            savings = (cache_read / 1_000_000) * (self.PRICE_INPUT_PER_MTK - self.PRICE_CACHE_READ_PER_MTK)
            logger.info(f"💰 Cache hit: {cache_read:,} tokens, saved ${savings:.4f}")

    def _calculate_operation_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_read: int,
        cache_write: int
    ) -> float:
        """Calculate cost for a single operation."""
        cost = (
            (input_tokens / 1_000_000) * self.PRICE_INPUT_PER_MTK +
            (output_tokens / 1_000_000) * self.PRICE_OUTPUT_PER_MTK +
            (cache_read / 1_000_000) * self.PRICE_CACHE_READ_PER_MTK +
            (cache_write / 1_000_000) * self.PRICE_CACHE_WRITE_PER_MTK
        )
        return round(cost, 6)

    def calculate_total_cost(self) -> float:
        """
        Calculate total cost in USD.

        Returns:
            Total cost for all recorded operations
        """
        return self._calculate_operation_cost(
            self.input_tokens,
            self.output_tokens,
            self.cache_read_tokens,
            self.cache_write_tokens
        )

    def calculate_cache_savings(self) -> float:
        """
        Calculate money saved by using prompt caching.

        Returns:
            Savings in USD from cache hits
        """
        # What we would have paid without caching
        would_have_paid = (self.cache_read_tokens / 1_000_000) * self.PRICE_INPUT_PER_MTK

        # What we actually paid with caching
        actually_paid = (self.cache_read_tokens / 1_000_000) * self.PRICE_CACHE_READ_PER_MTK

        return round(would_have_paid - actually_paid, 6)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive usage summary.

        Returns:
            Dictionary with usage stats and costs
        """
        total_cost = self.calculate_total_cost()
        cache_savings = self.calculate_cache_savings()
        elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "cache_read": self.cache_read_tokens,
                "cache_write": self.cache_write_tokens,
                "total": self.input_tokens + self.output_tokens
            },
            "costs": {
                "total_usd": round(total_cost, 4),
                "input_cost": round((self.input_tokens / 1_000_000) * self.PRICE_INPUT_PER_MTK, 4),
                "output_cost": round((self.output_tokens / 1_000_000) * self.PRICE_OUTPUT_PER_MTK, 4),
                "cache_read_cost": round((self.cache_read_tokens / 1_000_000) * self.PRICE_CACHE_READ_PER_MTK, 4),
                "cache_write_cost": round((self.cache_write_tokens / 1_000_000) * self.PRICE_CACHE_WRITE_PER_MTK, 4),
                "cache_savings_usd": round(cache_savings, 4)
            },
            "efficiency": {
                "cache_hit_rate": round(
                    self.cache_read_tokens / max(self.input_tokens + self.cache_read_tokens, 1) * 100,
                    1
                ),
                "cost_per_operation": round(total_cost / max(len(self.operations), 1), 4),
                "tokens_per_second": round((self.input_tokens + self.output_tokens) / max(elapsed, 1), 1)
            },
            "operations": {
                "total": len(self.operations),
                "duration_seconds": round(elapsed, 1)
            }
        }

    def get_detailed_breakdown(self) -> List[Dict]:
        """Get list of all individual operations with costs."""
        return self.operations.copy()

    def reset(self) -> None:
        """Reset all counters."""
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.operations = []
        self.start_time = datetime.now()
        logger.info("Usage tracker reset")

    def export_report(self, output_path: str) -> None:
        """
        Export usage report to JSON file.

        Args:
            output_path: Path to save report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "operations": self.operations
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Usage report exported to {output_path}")

    def print_summary(self) -> None:
        """Print formatted usage summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("API USAGE SUMMARY")
        print("=" * 60)

        print(f"\n📊 Token Usage:")
        print(f"  Input tokens:       {summary['tokens']['input']:>12,}")
        print(f"  Output tokens:      {summary['tokens']['output']:>12,}")
        print(f"  Cache reads:        {summary['tokens']['cache_read']:>12,}")
        print(f"  Cache writes:       {summary['tokens']['cache_write']:>12,}")
        print(f"  Total:              {summary['tokens']['total']:>12,}")

        print(f"\n💰 Costs:")
        print(f"  Input cost:         ${summary['costs']['input_cost']:>11.4f}")
        print(f"  Output cost:        ${summary['costs']['output_cost']:>11.4f}")
        print(f"  Cache read cost:    ${summary['costs']['cache_read_cost']:>11.4f}")
        print(f"  Cache write cost:   ${summary['costs']['cache_write_cost']:>11.4f}")
        print(f"  ─────────────────────────────")
        print(f"  Total cost:         ${summary['costs']['total_usd']:>11.4f}")
        print(f"  Cache savings:      ${summary['costs']['cache_savings_usd']:>11.4f}")

        print(f"\n⚡ Efficiency:")
        print(f"  Cache hit rate:     {summary['efficiency']['cache_hit_rate']:>11.1f}%")
        print(f"  Cost per operation: ${summary['efficiency']['cost_per_operation']:>11.4f}")
        print(f"  Tokens/second:      {summary['efficiency']['tokens_per_second']:>12.1f}")

        print(f"\n📈 Operations:")
        print(f"  Total operations:   {summary['operations']['total']:>12}")
        print(f"  Duration:           {summary['operations']['duration_seconds']:>11.1f}s")

        print("=" * 60 + "\n")


# ============================================================================
# GLOBAL TRACKER INSTANCE
# ============================================================================

_global_tracker: APIUsageTracker = None


def get_tracker() -> APIUsageTracker:
    """Get global usage tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = APIUsageTracker()
    return _global_tracker


def reset_tracker() -> None:
    """Reset global tracker."""
    global _global_tracker
    _global_tracker = APIUsageTracker()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create tracker
    tracker = APIUsageTracker()

    # Simulate some API calls
    class MockUsage:
        def __init__(self, input_tokens, output_tokens, cache_read=0, cache_write=0):
            self.input_tokens = input_tokens
            self.output_tokens = output_tokens
            self.cache_read_input_tokens = cache_read
            self.cache_creation_input_tokens = cache_write

    class MockResponse:
        def __init__(self, usage):
            self.usage = usage

    # First call - no cache
    response1 = MockResponse(MockUsage(10000, 2000, 0, 5000))
    tracker.record_usage(response1, "extract_project_info")

    # Second call - cache hit
    response2 = MockResponse(MockUsage(2000, 1500, 8000, 0))
    tracker.record_usage(response2, "extract_specifications")

    # Third call - another cache hit
    response3 = MockResponse(MockUsage(1500, 1000, 7500, 0))
    tracker.record_usage(response3, "extract_measurements")

    # Print summary
    tracker.print_summary()

    # Export report
    tracker.export_report("usage_report.json")
    print("Report exported to usage_report.json")
