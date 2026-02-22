import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import time

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

st.set_page_config(
    page_title="Gestor de Finanzas",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .category-header {
        background-color: #2E86C1;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .available-positive {
        color: #27AE60;
        font-weight: bold;
    }
    .available-negative {
        color: #E74C3C;
        font-weight: bold;
    }
    .stDataFrame {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONEXIÓN CON GOOGLE SHEETS
# ============================================================================

class GoogleSheetsManager:
    """
    Clase responsable de toda la comunicación con Google Sheets.
    Maneja la autenticación, lectura y escritura de datos.
    """
    
    def __init__(self, credentials_file, spreadsheet_name):
        """
        Inicializa la conexión con Google Sheets.
        
        Args:
            credentials_file: Ruta al archivo JSON de credenciales
            spreadsheet_name: Nombre del archivo de Google Sheets
        """
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file, self.scope
        )
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet = self.client.open(spreadsheet_name)
    
    def get_worksheet(self, worksheet_name):
        """Obtiene una hoja de cálculo específica."""
        return self.spreadsheet.worksheet(worksheet_name)
    
    def read_budget_data(self, worksheet_name="Presupuesto"):
        """
        Lee todos los datos del presupuesto desde Google Sheets.
        
        Returns:
            DataFrame con los datos del presupuesto
        """
        worksheet = self.get_worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    
    def read_transactions(self, worksheet_name="Transacciones"):
        """
        Lee el historial de transacciones desde Google Sheets.
        
        Returns:
            DataFrame con las transacciones
        """
        worksheet = self.get_worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    
    def update_expense(self, category, amount, worksheet_name="Presupuesto"):
        """
        Actualiza el gasto de una categoría específica.
        
        Args:
            category: Nombre de la categoría a actualizar
            amount: Nuevo monto de gasto
            worksheet_name: Nombre de la hoja
        """
        worksheet = self.get_worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Buscar la fila de la categoría
        category_col = df.columns[0]  # Primera columna es Categoría
        mask = df[category_col] == category
        
        if mask.any():
            row_index = df[mask].index[0] + 2  # +2 por header y índice 0
            # La columna de gasto es la tercera (índice 2)
            worksheet.update_cell(row_index, 3, amount)
            return True
        return False
    
    def add_transaction(self, date, category, description, amount, 
                        worksheet_name="Transacciones"):
        """
        Añade una nueva transacción al historial.
        
        Args:
            date: Fecha de la transacción
            category: Categoría del gasto
            description: Descripción del gasto
            amount: Monto de la transacción
            worksheet_name: Nombre de la hoja
        """
        worksheet = self.get_worksheet(worksheet_name)
        worksheet.append_row([date, category, description, amount])
    
    def get_categories(self, worksheet_name="Presupuesto"):
        """
        Obtiene lista de todas las categorías disponibles.
        
        Returns:
            Lista de nombres de categorías
        """
        df = self.read_budget_data(worksheet_name)
        return df.iloc[:, 0].tolist()

# ============================================================================
# LÓGICA DE NEGOCIO Y CÁLCULOS
# ============================================================================

class FinanceCalculator:
    """
    Clase que contiene toda la lógica de cálculos financieros.
    Maneja presupuestos, gastos, y cálculos de disponible.
    """
    
    @staticmethod
    def calculate_available(budget, spent):
        """
        Calcula el dinero disponible restando el gasto del presupuesto.
        
        Args:
            budget: Monto presupuestado
            spent: Monto gastado
            
        Returns:
            Diferencia entre presupuesto y gasto
        """
        try:
            budget_val = float(str(budget).replace('$', '').replace(',', ''))
            spent_val = float(str(spent).replace('$', '').replace(',', ''))
            return budget_val - spent_val
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def format_currency(amount):
        """
        Formatea un monto como moneda.
        
        Args:
            amount: Valor numérico a formatear
            
        Returns:
            String formateado como moneda
        """
        return f"${amount:,.2f}"
    
    @staticmethod
    def get_status_indicator(available):
        """
        Genera un indicador visual del estado financiero.
        
        Args:
            available: Monto disponible
            
        Returns:
            Emoji y texto descriptivo del estado
        """
        if available > 1000:
            return "🟢 Excel
