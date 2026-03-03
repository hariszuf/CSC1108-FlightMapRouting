# src/features/export_manager.py
import json
import csv
from typing import Dict, Any, Optional, List
from io import StringIO
from datetime import datetime
from src.models import RouteResult

class ExportManager:
    """Export routes in various formats"""
    
    def export_as_json(self, route_result: RouteResult) -> str:
        """Export route as JSON"""
        data = {
            'route': {
                'path': route_result.path,
                'hops': route_result.hops,
                'total_km': route_result.total_km,
                'total_minutes': route_result.total_minutes,
                'total_price': route_result.total_price,
                'timestamp': datetime.now().isoformat()
            },
            'segments': self._get_segments(route_result)
        }
        return json.dumps(data, indent=2)
    
    def export_as_csv(self, route_result: RouteResult) -> str:
        """Export route as CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Segment', 'From', 'To', 'Distance (km)', 'Time (min)', 'Price ($)'])
        
        # Write segments
        segments = self._get_segments(route_result)
        for i, seg in enumerate(segments, 1):
            writer.writerow([
                f"Segment {i}",
                seg['from'],
                seg['to'],
                seg['distance'],
                seg['time'],
                seg['price']
            ])
        
        # Write summary
        writer.writerow([])
        writer.writerow(['SUMMARY', '', '', '', '', ''])
        writer.writerow(['Total', '', '', 
                        route_result.total_km,
                        route_result.total_minutes,
                        route_result.total_price])
        
        return output.getvalue()
    
    def export_as_text(self, route_result: RouteResult) -> str:
        """Export route as plain text"""
        lines = []
        lines.append("=" * 50)
        lines.append("FLIGHT ROUTE DETAILS")
        lines.append("=" * 50)
        lines.append(f"Route: {route_result.pretty()}")
        lines.append(f"Total connections: {route_result.hops}")
        lines.append(f"Total distance: {route_result.total_km:.2f} km")
        lines.append(f"Total time: {route_result.total_minutes} minutes")
        lines.append(f"Total price: ${route_result.total_price:.2f}")
        lines.append("=" * 50)
        lines.append("\nSegment Details:")
        
        segments = self._get_segments(route_result)
        for i, seg in enumerate(segments, 1):
            lines.append(f"\n  Segment {i}: {seg['from']} → {seg['to']}")
            lines.append(f"    Distance: {seg['distance']:.2f} km")
            lines.append(f"    Time: {seg['time']} min")
            lines.append(f"    Price: ${seg['price']:.2f}")
        
        lines.append("\n" + "=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def export_as_pdf(self, route_result: RouteResult) -> Optional[bytes]:
        """Export route as PDF (requires additional libraries)"""
        # Return None instead of trying to import pdfkit
        print("PDF export requires additional libraries (reportlab/weasyprint/pdfkit)")
        return None
    
    def create_shareable_link(self, route_result: RouteResult) -> str:
        """Create a shareable link for the route"""
        # Encode route data in a simple format
        route_str = '-'.join(route_result.path)
        base_url = "https://flightroute.pro/share/"
        return f"{base_url}{route_str}"
    
    def _get_segments(self, route_result: RouteResult) -> List[Dict]:
        """Extract segment details from route result"""
        segments = []
        # Note: This assumes we don't have per-segment data in RouteResult
        # In a real implementation, you might want to store segment details
        num_segments = len(route_result.path) - 1
        if num_segments == 0:
            return segments
            
        for i in range(num_segments):
            segments.append({
                'from': route_result.path[i],
                'to': route_result.path[i + 1],
                'distance': route_result.total_km / num_segments,  # Approximate
                'time': route_result.total_minutes // num_segments,  # Approximate
                'price': route_result.total_price / num_segments  # Approximate
            })
        return segments