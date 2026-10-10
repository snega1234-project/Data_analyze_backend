import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import matplotlib
matplotlib.use('Agg') # Ensure it doesn't try to open a GUI window

class DataAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        try:
            if file_path.endswith('.csv'):
                raw_df = pd.read_csv(file_path, header=None)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                raw_df = pd.read_excel(file_path, header=None)
            else:
                raise ValueError("Unsupported file format. Please upload CSV or Excel.")
        except pd.errors.EmptyDataError:
            raise ValueError("The uploaded file is completely empty (zero bytes). Please upload a valid dataset.")
        except pd.errors.ParserError:
            raise ValueError("The uploaded file is corrupted or malformed. Please check the file contents.")
        except Exception as e:
            # Handle corrupted excel files (which throw zipfile.BadZipFile or similar)
            if "BadZipFile" in str(type(e)):
                raise ValueError("The uploaded file is a corrupted Excel file. Please upload a valid dataset.")
            raise ValueError(f"Failed to read file: {str(e)}")
            
        if len(raw_df) == 0:
            self.df = pd.DataFrame()
        else:
            # Auto-detect header row: find the first row with the maximum number of non-null values
            # This skips over title/metadata rows in messy Excel/CSV files
            valid_counts = raw_df.notna().sum(axis=1)
            header_idx = valid_counts.idxmax()
            
            self.df = raw_df.iloc[header_idx + 1:].reset_index(drop=True)
            self.df.columns = raw_df.iloc[header_idx].astype(str)
            
        if len(self.df) == 0:
            raise ValueError("The dataset contains columns but no data rows. Please upload a file with data.")

    def get_columns(self):
        """Return the column names as a list."""
        return self.df.columns.tolist()

    def generate_chart(self, chart_type, x_field, y_field=None):
        """
        Data manipulation and visualization.
        """
        plt.figure(figsize=(10, 6))
        # Use a modern style and adjust colors for a premium dark mode look
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#1e1e2f", "figure.facecolor": "#1e1e2f"})

        # Data manipulation: Handle missing values (NA or blank cells)
        cols = [x_field]
        if y_field:
            cols.append(y_field)
            
        # Create a copy, replace empty whitespace strings with proper NA, and drop rows with missing values in our target columns
        plot_df = self.df.copy()
        plot_df[cols] = plot_df[cols].replace(r'^\s*$', pd.NA, regex=True)
        plot_df = plot_df.dropna(subset=cols)
        
        if len(plot_df) == 0:
            raise ValueError("All data rows for the selected fields contain missing or empty values. Cannot generate a chart.")

        if y_field:
            if x_field == y_field:
                raise ValueError("X-Axis and Y-Axis cannot be the same. Please select different fields or leave Y-Axis blank.")
            
            # Attempt to clean and convert Y to numeric to handle messy data (e.g., "$250.00", " 250 ", "1,000")
            if not pd.api.types.is_numeric_dtype(plot_df[y_field]):
                clean_series = plot_df[y_field].astype(str).str.replace(r'[$, ]', '', regex=True)
                converted = pd.to_numeric(clean_series, errors='coerce')
                # If we successfully extracted numbers, update the column
                if converted.notna().sum() > 0:
                    plot_df[y_field] = converted
                elif chart_type in ['bar', 'line', 'scatter']:
                    raise ValueError(f"Y-Axis ('{y_field}') must be numeric for {chart_type.capitalize()} charts.")

        # Advanced Data Manipulation using Pandas
        if y_field and pd.api.types.is_numeric_dtype(plot_df[y_field]):
            # Validate Pie Chart raw data before aggregation hides negative values
            if chart_type == 'pie':
                if (plot_df[y_field] < 0).any():
                    raise ValueError(f"Pie charts cannot display negative values. The field '{y_field}' contains negative numbers in the dataset.")
                if (plot_df[y_field] == 0).all():
                    raise ValueError(f"All values in '{y_field}' are exactly zero. Cannot generate a Pie chart from zero-only data.")

            if chart_type in ['bar', 'pie']:
                # 1. Group by X and aggregate (sum) Y for categorical charts
                agg_df = plot_df.groupby(x_field)[y_field].sum().reset_index()
                # 2. Sort by Y descending to show most significant data first
                agg_df = agg_df.sort_values(by=y_field, ascending=False)
                
                # 3. Limit to top 20 categories to keep the chart readable
                if len(agg_df) > 20:
                    agg_df = agg_df.head(20)
                    
                plot_df = agg_df
            elif chart_type == 'line':
                # For line charts, sort by X-axis to prevent zigzag lines. Seaborn handles its own mean aggregation.
                plot_df = plot_df.sort_values(by=x_field)
            # Scatter and Histogram retain the raw un-aggregated plot_df to show individual data points

        # Generate chart based on user choice
        color_palette = "mako" # Nice vibrant palette
        
        if chart_type == 'bar':
            if y_field:
                # Color code based on value: green for positive, red for negative, grey for zero
                bar_colors = {row[x_field]: '#10b981' if row[y_field] > 0 else '#ef4444' if row[y_field] < 0 else '#9ca3af' for _, row in plot_df.iterrows()}
                sns.barplot(data=plot_df, x=x_field, y=y_field, hue=x_field, palette=bar_colors, legend=False)
            else:
                # If no Y-axis is given, calculate counts, SORT descending, and limit to top 20
                counts_df = plot_df[x_field].value_counts().reset_index()
                counts_df.columns = [x_field, 'Count']
                if len(counts_df) > 20:
                    counts_df = counts_df.head(20)
                sns.barplot(data=counts_df, x=x_field, y='Count', hue=x_field, palette=color_palette, legend=False)
                y_field = 'Count' # Update label for the plot
            plt.xticks(rotation=45, ha='right')
        elif chart_type == 'line':
            sns.lineplot(data=plot_df, x=x_field, y=y_field, color="#00f2fe", linewidth=2.5)
            plt.xticks(rotation=45, ha='right')
        elif chart_type == 'scatter':
            sns.scatterplot(data=plot_df, x=x_field, y=y_field, color="#4facfe", s=100, alpha=0.8)
        elif chart_type == 'histogram':
            sns.histplot(data=plot_df, x=x_field, color="#f093fb", kde=True)
            plt.xticks(rotation=45, ha='right')
        elif chart_type == 'pie':
            if y_field and pd.api.types.is_numeric_dtype(plot_df[y_field]):
                # If Y is provided and numeric, use the manipulated Y values for pie slices
                values = plot_df[y_field]
                labels = plot_df[x_field]
            else:
                # Otherwise, count occurrences of X
                counts = plot_df[x_field].value_counts()
                if len(counts) > 20:
                    counts = counts.head(20)
                values = counts.values
                labels = counts.index
                
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, 
                    colors=sns.color_palette(color_palette, len(values)),
                    textprops={'color': '#e0e0e0', 'fontsize': 11})
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
            
        plt.title(f"{chart_type.capitalize()} Chart", color="white", fontsize=16, pad=20)
        plt.xlabel(x_field, color="#a0a0b0", fontsize=12)
        if y_field:
            plt.ylabel(y_field, color="#a0a0b0", fontsize=12)
            
        # Customize tick colors
        plt.tick_params(colors="#a0a0b0")

        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True, dpi=150)
        buf.seek(0)
        plt.close()
        
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{image_base64}"
