"""CLI: print the unit-circle degree table and plot it.

Run with ``python unit_circle.py``. Prints the analysis, opens the plot,
then offers to save it as ``unit_circle_degrees.png`` in the current
directory.
"""

from fielder_intercept.unit_circle import (
    DEGREES,
    format_degree_analysis,
    plot_unit_circle_with_degrees,
)


def main() -> None:
    import matplotlib.pyplot as plt

    print(format_degree_analysis(DEGREES))
    plot_unit_circle_with_degrees(DEGREES)
    plt.show()

    save_plot = input("\nWould you like to save this plot? (y/n): ").lower().strip()
    if save_plot == "y":
        filename = "unit_circle_degrees.png"
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"Plot saved as {filename}")


if __name__ == "__main__":
    main()
