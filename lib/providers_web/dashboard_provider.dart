import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';
import '../../core/constants/api_constants.dart';

class WebDashboardProvider extends ChangeNotifier {
  // KPIs
  int totalProducts = 0;
  int criticalStock = 0;
  int todayMovements = 0;
  double inventoryValue = 0.0;

  // Gráficas
  Map<String, int> movementChartData = {};
  Map<String, int> categoryChartData = {};

  // Alertas
  List<Map<String, dynamic>> alerts = [];

  // Estados
  bool isLoading = true;
  bool isLoadingMovement = true;
  bool isLoadingCategory = true;
  bool isLoadingAlerts = true;
  String? error;

  Future<void> loadDashboard() async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final data = await ApiService.get(ApiConstants.dashboard);

      if (data['kpis'] != null) {
        totalProducts = data['kpis']['total_products'] ?? 0;
        criticalStock = data['kpis']['critical_stock'] ?? 0;
        todayMovements = data['kpis']['today_movements'] ?? 0;
        inventoryValue = (data['kpis']['inventory_value'] ?? 0.0).toDouble();
      }

      isLoading = false;
      notifyListeners();
    } catch (e) {
      error = e.toString().replaceFirst('Exception: ', '');
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadMovementChart() async {
    isLoadingMovement = true;
    notifyListeners();

    try {
      movementChartData = {
        'Ene': 45,
        'Feb': 52,
        'Mar': 48,
        'Abr': 61,
        'May': 55,
        'Jun': 67,
        'Jul': 72,
        'Ago': 68,
        'Sep': 58,
        'Oct': 63,
        'Nov': 71,
        'Dic': 82,
      };

      isLoadingMovement = false;
      notifyListeners();
    } catch (e) {
      isLoadingMovement = false;
      notifyListeners();
    }
  }

  Future<void> loadCategoryChart() async {
    isLoadingCategory = true;
    notifyListeners();

    try {
      categoryChartData = {
        'Medicamentos': 120,
        'Equipos': 45,
        'Insumos': 89,
        'Material': 34,
      };

      isLoadingCategory = false;
      notifyListeners();
    } catch (e) {
      isLoadingCategory = false;
      notifyListeners();
    }
  }

  Future<void> loadAlerts() async {
    isLoadingAlerts = true;
    notifyListeners();

    try {
      final data = await ApiService.get(
          '${ApiConstants.alerts}?is_resolved=false&limit=20');

      if (data['items'] != null) {
        alerts = List<Map<String, dynamic>>.from(data['items']);
      }

      isLoadingAlerts = false;
      notifyListeners();
    } catch (e) {
      isLoadingAlerts = false;
      notifyListeners();
    }
  }

  Future<void> resolveAlert(int alertId) async {
    try {
      await ApiService.post('/api/alerts/$alertId/resolve', {});
      await loadAlerts();
      await loadDashboard();
    } catch (e) {
      debugPrint('Error al resolver alerta: $e');
    }
  }
}
