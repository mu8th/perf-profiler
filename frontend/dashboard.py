"""Dashboard rendering module for Perf Profiler frontend."""

from __future__ import annotations

from typing import Any


class Dashboard:
    """Render dashboard sections from profile and metric data."""

    def render_flame_graph(self, profiles: list[dict[str, Any]]) -> str:
        """Generate flame graph drawing instructions from profile data.

        Args:
            profiles: List of function call profiles with CPU time values.

        Returns:
            JSON string containing canvas drawing commands.
        """
        if not profiles or len(profiles) == 0:
            return '{"command": "draw_text", "text": "No data available"}'

        total_cpu = sum(p["cpu_time"] for p in profiles)
        sorted_profiles = sorted(profiles, key=lambda p: p["cpu_time"], reverse=True)

        commands = []
        y_position = 380
        for profile in sorted_profiles:
            width = (profile["cpu_time"] / total_cpu) * 800
            commands.append({
                "command": "fill_rect",
                "x": 10,
                "y": y_position - 20,
                "width": width,
                "height": 20,
                "color": "#4f46e5"
            })
            commands.append({
                "command": "draw_text",
                "x": 15,
                "y": y_position - 10,
                "text": profile["function_name"]
            })
            y_position -= 25

        return '{"commands": ' + str(commands) + '}'

    def render_hot_paths_table(self, hot_paths: list[dict[str, Any]]) -> str:
        """Generate HTML table rows for hot path data.

        Args:
            hot_paths: List of detected hot path entries with percentage values.

        Returns:
            HTML string containing tr elements with function names and metrics.
        """
        if not hot_paths or len(hot_paths) == 0:
            return '<tr><td colspan="4">No hot paths detected</td></tr>'

        sorted_hot_paths = sorted(
            hot_paths,
            key=lambda hp: hp["percentage_of_total"],
            reverse=True
        )

        html = ""
        for hp in sorted_hot_paths:
            avg_cpu_time = hp.get("avg_cpu_time", 0)
            call_count = hp.get("call_count", 0)
            html += (
                f'<tr><td>{hp["function_name"]}</td>'
                f'<td>{avg_cpu_time}s</td>'
                f'<td>{call_count}</td>'
                f'<td>{hp["percentage_of_total"]}%</td></tr>'
            )

        return html

    def render_memory_chart(self, snapshots: list[dict[str, Any]]) -> str:
        """Generate memory trend canvas drawing instructions.

        Args:
            snapshots: List of memory allocation snapshots with timestamps.

        Returns:
            JSON string containing canvas stroke commands.
        """
        if not snapshots or len(snapshots) == 0:
            return '{"command": "draw_text", "text": "No data available"}'

        sorted_snapshots = sorted(
            snapshots,
            key=lambda s: s["timestamp"]
        )

        commands = [{"command": "begin_path"}]
        first_point = True
        for snapshot in sorted_snapshots:
            x = ((snapshot["timestamp"] % 3600) / 3600 * 800)
            y = (snapshot["current_bytes"] / max(1, snapshot["peak_bytes"]) * 300)
            if first_point:
                commands.append({"command": "move_to", "x": x, "y": y})
                first_point = False
            else:
                commands.append({"command": "line_to", "x": x, "y": y})

        commands.append({"command": "stroke"})

        return '{"commands": ' + str(commands) + '}'


def update_metrics_display(data: dict[str, Any]) -> str:
    """Generate formatted HTML string for live metrics display.

    Args:
        data: Current metric values dictionary with cpu_time and memory_bytes keys.

    Returns:
        HTML string containing span elements with metric values.
    """
    cpu_span = f'<span>CPU: {data.get("cpu_time", 0)}s</span>'
    memory_span = f'<span>Memory: {data.get("memory_bytes", 0)} bytes</span>'

    return cpu_span + memory_span