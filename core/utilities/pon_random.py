"""
PON Random Variables
Generadores de variables aleatorias integrados de netPONPy
"""

import numpy as np


class ExpVariable:
    """Variable aleatoria exponencial para modelar llegadas de tráfico"""
    
    def __init__(self, seed: int = 1234567, rate: float = 10):
        """
        Inicializar variable exponencial
        
        Args:
            seed: Semilla para el generador de números aleatorios
            rate: Tasa (lambda) de la distribución exponencial
        """
        if rate <= 0:
            raise ValueError("rate parameter must be positive.")
        
        self.rate = rate
        self.seed = seed
        
        # Crear generador independiente para esta variable
        self._rng = np.random.RandomState(seed)

    def getNextValue(self) -> float:
        """
        Obtener siguiente valor exponencial
        
        Returns:
            Valor generado según distribución exponencial
        """
        value = self._rng.exponential(scale=1 / self.rate, size=1)
        return value.item()
    
    def get_statistics(self) -> dict:
        """Obtener estadísticas teóricas de la distribución"""
        return {
            'rate': self.rate,
            'mean': 1 / self.rate,
            'variance': 1 / (self.rate ** 2),
            'std': 1 / self.rate,
            'seed': self.seed
        }


class UniformVariable:
    """Variable aleatoria uniforme"""
    
    def __init__(self, seed: int = 1234567, min_val: float = 0.0, max_val: float = 1.0):
        """
        Inicializar variable uniforme
        
        Args:
            seed: Semilla para el generador
            min_val: Valor mínimo
            max_val: Valor máximo
        """
        if min_val >= max_val:
            raise ValueError("min_val must be less than max_val")
            
        self.min_val = min_val
        self.max_val = max_val
        self.seed = seed
        
        # Crear generador independiente
        self._rng = np.random.RandomState(seed)

    def getNextValue(self) -> float:
        """
        Obtener siguiente valor uniforme
        
        Returns:
            Valor generado según distribución uniforme
        """
        return self._rng.uniform(self.min_val, self.max_val)
    
    def get_statistics(self) -> dict:
        """Obtener estadísticas teóricas de la distribución"""
        mean = (self.min_val + self.max_val) / 2
        variance = ((self.max_val - self.min_val) ** 2) / 12
        
        return {
            'min_val': self.min_val,
            'max_val': self.max_val,
            'mean': mean,
            'variance': variance,
            'std': np.sqrt(variance),
            'seed': self.seed
        }