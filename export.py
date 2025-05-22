import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
from io import BytesIO
from fpdf import FPDF


def export_to_excel(df, filename=None):
    """
    Export DataFrame to Excel file
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the Excel file
        
    Returns:
        str: Path to the saved file
    """
    if filename is None:
        filename = f"stock_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Create 'exports' directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    
    # Full path for the file
    file_path = os.path.join('exports', filename)
    
    # Save DataFrame to Excel
    df.to_excel(file_path, index=True)
    
    return file_path


def export_to_csv(df, filename=None):
    """
    Export DataFrame to CSV file
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str, optional): Filename for the CSV file
        
    Returns:
        str: Path to the saved file
    """
    if filename is None:
        filename = f"stock_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Create 'exports' directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    
    # Full path for the file
    file_path = os.path.join('exports', filename)
    
    # Save DataFrame to CSV
    df.to_csv(file_path, index=True)
    
    return file_path


def export_to_pdf(df, symbol, chart_fig=None, filename=None):
    """
    Export DataFrame and chart to PDF
    
    Args:
        df (pd.DataFrame): DataFrame to export
        symbol (str): Stock symbol
        chart_fig (plotly.graph_objects.Figure, optional): Plotly figure to include
        filename (str, optional): Filename for the PDF
        
    Returns:
        str: Path to the saved file
    """
    if filename is None:
        filename = f"{symbol}_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Create 'exports' directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    
    # Full path for the file
    file_path = os.path.join('exports', filename)
    
    # Create PDF
    pdf = FPDF()
    
    # Add first page
    pdf.add_page()
    
    # Set font
    pdf.set_font('Arial', 'B', 16)
    
    # Title
    pdf.cell(0, 10, f'{symbol} Stock Analysis Report', 0, 1, 'C')
    pdf.ln(10)
    
    # Date
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'R')
    pdf.ln(5)
    
    # Add chart if provided
    if chart_fig is not None:
        # Save the figure to a temporary file
        img_path = os.path.join('exports', 'temp_chart.png')
        
        # If it's a plotly figure, convert it to an image
        if hasattr(chart_fig, 'write_image'):
            chart_fig.write_image(img_path, width=800, height=400)
            
            # Add the image to the PDF
            pdf.image(img_path, x=10, y=40, w=190)
            pdf.ln(120)  # Move down after image
        
        # Clean up temporary file
        if os.path.exists(img_path):
            os.remove(img_path)
    
    # Add table headers
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Date', 1, 0, 'C')
    pdf.cell(30, 10, 'Open', 1, 0, 'C')
    pdf.cell(30, 10, 'High', 1, 0, 'C')
    pdf.cell(30, 10, 'Low', 1, 0, 'C')
    pdf.cell(30, 10, 'Close', 1, 0, 'C')
    pdf.cell(30, 10, 'Volume', 1, 1, 'C')
    
    # Add data rows
    pdf.set_font('Arial', '', 8)
    
    # Get the last 20 rows of data (or all if less than 20)
    display_df = df.tail(20).reset_index()
    
    for _, row in display_df.iterrows():
        # Format date
        date_str = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], datetime.datetime) else str(row['Date'])
        
        pdf.cell(40, 6, date_str, 1, 0, 'L')
        pdf.cell(30, 6, f"{row['Open']:.2f}", 1, 0, 'R')
        pdf.cell(30, 6, f"{row['High']:.2f}", 1, 0, 'R')
        pdf.cell(30, 6, f"{row['Low']:.2f}", 1, 0, 'R')
        pdf.cell(30, 6, f"{row['Close']:.2f}", 1, 0, 'R')
        pdf.cell(30, 6, f"{int(row['Volume']):,}", 1, 1, 'R')
    
    # Save PDF
    pdf.output(file_path)
    
    return file_path


def get_download_link(file_path, link_text=None):
    """
    Generate HTML download link for a file
    
    Args:
        file_path (str): Path to the file
        link_text (str, optional): Text to display for the link
        
    Returns:
        str: HTML for the download link
    """
    import base64
    
    if link_text is None:
        link_text = os.path.basename(file_path)
    
    with open(file_path, "rb") as file:
        encoded_file = base64.b64encode(file.read()).decode()
    
    file_type = file_path.split('.')[-1]
    if file_type == 'xlsx':
        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif file_type == 'csv':
        mime_type = 'text/csv'
    elif file_type == 'pdf':
        mime_type = 'application/pdf'
    elif file_type == 'jpg' or file_type == 'jpeg':
        mime_type = 'image/jpeg'
    else:
        mime_type = 'application/octet-stream'
    
    href = f'data:{mime_type};base64,{encoded_file}'
    
    return f'<a href="{href}" download="{link_text}">{link_text}</a>'