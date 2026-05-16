import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../../providers/auth_provider.dart';
import '../../../../providers_web/dashboard_provider.dart';
import '../../../../core/constants/app_colors.dart';

class WebDashboardScreen extends StatefulWidget {
  const WebDashboardScreen({super.key});

  @override
  State<WebDashboardScreen> createState() => _WebDashboardScreenState();
}

class _WebDashboardScreenState extends State<WebDashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider =
          Provider.of<WebDashboardProvider>(context, listen: false);
      provider.loadDashboard();
      provider.loadMovementChart();
      provider.loadCategoryChart();
      provider.loadAlerts();
    });
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final dashboardProvider = Provider.of<WebDashboardProvider>(context);
    final user = authProvider.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Panel Administrativo'),
        elevation: 0,
        backgroundColor: AppColors.primary,
        actions: [
          if (user != null)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: [
                  const Icon(Icons.person, size: 16, color: Colors.white),
                  const SizedBox(width: 4),
                  Text(
                    user.fullName,
                    style: const TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await authProvider.logout();
              if (mounted) {
                Navigator.pushReplacementNamed(context, '/web/login');
              }
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: dashboardProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : dashboardProvider.error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(dashboardProvider.error!),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          dashboardProvider.loadDashboard();
                          dashboardProvider.loadMovementChart();
                          dashboardProvider.loadCategoryChart();
                          dashboardProvider.loadAlerts();
                        },
                        child: const Text('Reintentar'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    await dashboardProvider.loadDashboard();
                    await dashboardProvider.loadMovementChart();
                    await dashboardProvider.loadCategoryChart();
                    await dashboardProvider.loadAlerts();
                  },
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // KPIs Grid
                        GridView.count(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          crossAxisCount: _getCrossAxisCount(context),
                          crossAxisSpacing: 16,
                          mainAxisSpacing: 16,
                          childAspectRatio: 1.5,
                          children: [
                            _buildKpiCard(
                              title: 'Total Productos',
                              value: dashboardProvider.totalProducts.toString(),
                              icon: Icons.inventory,
                              color: AppColors.primary,
                            ),
                            _buildKpiCard(
                              title: 'Stock Crítico',
                              value: dashboardProvider.criticalStock.toString(),
                              icon: Icons.warning_amber,
                              color: Colors.red,
                            ),
                            _buildKpiCard(
                              title: 'Movimientos Hoy',
                              value:
                                  dashboardProvider.todayMovements.toString(),
                              icon: Icons.trending_up,
                              color: Colors.green,
                            ),
                            _buildKpiCard(
                              title: 'Valor Inventario',
                              value:
                                  'Bs. ${dashboardProvider.inventoryValue.toStringAsFixed(2)}',
                              icon: Icons.attach_money,
                              color: Colors.orange,
                            ),
                          ],
                        ),

                        const SizedBox(height: 24),

                        // Gráficas
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: _buildChartCard(
                                title: 'Movimientos del Último Mes',
                                child: dashboardProvider.isLoadingMovement
                                    ? const Center(
                                        child: CircularProgressIndicator())
                                    : dashboardProvider
                                            .movementChartData.isEmpty
                                        ? const Center(child: Text('Sin datos'))
                                        : _buildMovementChart(dashboardProvider
                                            .movementChartData),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: _buildChartCard(
                                title: 'Stock por Categoría',
                                child: dashboardProvider.isLoadingCategory
                                    ? const Center(
                                        child: CircularProgressIndicator())
                                    : dashboardProvider
                                            .categoryChartData.isEmpty
                                        ? const Center(child: Text('Sin datos'))
                                        : _buildCategoryChart(dashboardProvider
                                            .categoryChartData),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 24),

                        // Alertas Activas
                        _buildAlertsTable(dashboardProvider),
                      ],
                    ),
                  ),
                ),
    );
  }

  int _getCrossAxisCount(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width >= 1200) return 4;
    if (width >= 800) return 2;
    return 1;
  }

  Widget _buildKpiCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, size: 24, color: color),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartCard({
    required String title,
    required Widget child,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(height: 250, child: child),
          ],
        ),
      ),
    );
  }

  Widget _buildMovementChart(Map<String, int> data) {
    final months = data.keys.toList();
    final values = data.values.toList();

    if (months.isEmpty) return const Center(child: Text('Sin datos'));

    final maxValue = values.reduce((a, b) => a > b ? a : b);

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: List.generate(months.length, (index) {
          final double height =
              maxValue > 0 ? (values[index] / maxValue) * 180 : 0;

          return Container(
            width: 60,
            margin: const EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Container(
                  height: height,
                  width: 40,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Center(
                    child: Text(
                      values[index].toString(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Transform.rotate(
                  angle: -0.5,
                  child: Text(
                    months[index],
                    style: const TextStyle(fontSize: 10),
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildCategoryChart(Map<String, int> data) {
    final categories = data.keys.toList();
    final values = data.values.toList();

    if (categories.isEmpty) return const Center(child: Text('Sin datos'));

    final maxValue = values.reduce((a, b) => a > b ? a : b);

    return ListView.builder(
      itemCount: categories.length,
      itemBuilder: (context, index) {
        final double percentage =
            maxValue > 0 ? (values[index] / maxValue) * 100 : 0;

        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              SizedBox(
                width: 100,
                child: Text(
                  categories[index],
                  style: const TextStyle(fontSize: 12),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      height: 24,
                      width: percentage,
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(
                values[index].toString(),
                style: const TextStyle(fontSize: 12),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAlertsTable(WebDashboardProvider provider) {
    if (provider.isLoadingAlerts) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (provider.alerts.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(
            child: Column(
              children: [
                Icon(Icons.notifications_none, size: 48, color: Colors.grey),
                SizedBox(height: 16),
                Text('No hay alertas activas'),
              ],
            ),
          ),
        ),
      );
    }

    return Card(
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columnSpacing: 16,
          columns: const [
            DataColumn(label: Text('Tipo')),
            DataColumn(label: Text('Título')),
            DataColumn(label: Text('Mensaje')),
            DataColumn(label: Text('Severidad')),
            DataColumn(label: Text('Fecha')),
            DataColumn(label: Text('Acciones')),
          ],
          rows: provider.alerts.map((alert) {
            Color severityColor;
            switch (alert['severity']) {
              case 'critical':
                severityColor = Colors.red;
                break;
              case 'high':
                severityColor = Colors.orange;
                break;
              default:
                severityColor = Colors.blue;
                break;
            }

            return DataRow(
              cells: [
                DataCell(Text(alert['alert_type'] ?? 'N/A')),
                DataCell(Text(alert['title'],
                    style: const TextStyle(fontWeight: FontWeight.w500))),
                DataCell(Text(alert['message'],
                    maxLines: 1, overflow: TextOverflow.ellipsis)),
                DataCell(
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: severityColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      alert['severity'],
                      style: TextStyle(color: severityColor, fontSize: 12),
                    ),
                  ),
                ),
                DataCell(
                    Text(_formatDate(DateTime.parse(alert['created_at'])))),
                DataCell(
                  Row(
                    children: [
                      if (!alert['is_resolved'])
                        IconButton(
                          icon: const Icon(Icons.check_circle, size: 20),
                          color: Colors.green,
                          onPressed: () => provider.resolveAlert(alert['id']),
                        ),
                    ],
                  ),
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
