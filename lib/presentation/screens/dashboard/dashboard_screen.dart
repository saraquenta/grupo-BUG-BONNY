import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_strings.dart';
import '../../../data/models/user_model.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/role_badge.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user!;

    return Scaffold(
      appBar: _buildAppBar(context, user),
      drawer: _buildDrawer(context, user),
      body: RefreshIndicator(
        onRefresh: () async {},   // Se conectará a la API en el Día 5
        color: AppColors.primary,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _GreetingCard(user: user),
              const SizedBox(height: 20),
              _buildSectionTitle('Resumen de Inventario'),
              const SizedBox(height: 12),
              _buildKpiGrid(),
              const SizedBox(height: 24),
              _buildSectionTitle('Acciones Rápidas'),
              const SizedBox(height: 12),
              _buildQuickActions(context, user),
              const SizedBox(height: 24),
              _buildSectionTitle('Actividad Reciente'),
              const SizedBox(height: 12),
              _buildRecentActivity(),
              const SizedBox(height: 24),
              const _ModulesBanner(),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  AppBar _buildAppBar(BuildContext context, UserModel user) {
    return AppBar(
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            AppStrings.appName,
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
          ),
          Text(
            AppStrings.company,
            style: const TextStyle(fontSize: 11, color: Colors.white70),
          ),
        ],
      ),
      actions: [
        Stack(
          children: [
            IconButton(
              icon: const Icon(Icons.notifications_outlined),
              onPressed: () {},
            ),
            Positioned(
              right: 10,
              top:   10,
              child: Container(
                width:  8,
                height: 8,
                decoration: const BoxDecoration(
                  color:  AppColors.danger,
                  shape:  BoxShape.circle,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(width: 4),
      ],
    );
  }

  Widget _buildDrawer(BuildContext context, UserModel user) {
    final auth = context.read<AuthProvider>();

    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          // Header del drawer
          UserAccountsDrawerHeader(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.primaryDark, AppColors.primary],
              ),
            ),
            accountName: Text(
              user.fullName,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            accountEmail: Text(
              user.email,
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
            currentAccountPicture: CircleAvatar(
              backgroundColor: Colors.white,
              child: Text(
                user.initials,
                style: TextStyle(
                  color:      user.roleColor,
                  fontSize:   22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            otherAccountsPictures: [
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  user.roleLabel,
                  style: const TextStyle(fontSize: 10, color: Colors.white),
                ),
              ),
            ],
          ),

          _DrawerItem(
            icon:     Icons.dashboard_rounded,
            label:    AppStrings.dashboard,
            isActive: true,
            onTap:    () => Navigator.pop(context),
          ),
          _DrawerItem(
            icon:  Icons.inventory_2_outlined,
            label: AppStrings.products,
            onTap: () {},      // Módulo Día 3
          ),
          _DrawerItem(
            icon:  Icons.add_box_outlined,
            label: AppStrings.ingresos,
            onTap: () {},      // Módulo Día 4
          ),
          _DrawerItem(
            icon:  Icons.outbox_outlined,
            label: AppStrings.salidas,
            onTap: () {},      // Módulo Día 4
          ),
          _DrawerItem(
            icon:  Icons.qr_code_scanner_rounded,
            label: AppStrings.scannerQR,
            onTap: () {},      // Módulo Día 3
          ),
          _DrawerItem(
            icon:  Icons.notifications_outlined,
            label: AppStrings.alerts,
            onTap: () {},      // Módulo Día 5
          ),
          _DrawerItem(
            icon:  Icons.bar_chart_rounded,
            label: AppStrings.reports,
            onTap: () {},      // Módulo Día 6
          ),

          if (user.isAdmin) ...[
            const Divider(indent: 16, endIndent: 16),
            _DrawerItem(
              icon:  Icons.people_outline,
              label: AppStrings.users,
              onTap: () {},    // Módulo Día 2
            ),
            _DrawerItem(
              icon:  Icons.settings_outlined,
              label: AppStrings.settings,
              onTap: () {},
            ),
          ],

          const Divider(indent: 16, endIndent: 16),

          _DrawerItem(
            icon:  Icons.logout_rounded,
            label: AppStrings.logout,
            color: AppColors.danger,
            onTap: () async {
              Navigator.pop(context);
              await auth.logout();
            },
          ),

          const SizedBox(height: 16),
          Center(
            child: Text(
              '${AppStrings.version} · ${AppStrings.university}',
              style: const TextStyle(
                color:    AppColors.textHint,
                fontSize: 10,
              ),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize:   16,
        fontWeight: FontWeight.bold,
        color:      AppColors.textPrimary,
      ),
    );
  }

  Widget _buildKpiGrid() {
    return GridView.count(
      shrinkWrap:   true,
      physics:      const NeverScrollableScrollPhysics(),
      crossAxisCount:   2,
      crossAxisSpacing: 12,
      mainAxisSpacing:  12,
      childAspectRatio: 1.25,
      children: const [
        _KpiCard(
          label: AppStrings.totalProducts,
          value: '—',
          icon:  Icons.inventory_2_rounded,
          color: AppColors.primary,
        ),
        _KpiCard(
          label: AppStrings.criticalStock,
          value: '—',
          icon:  Icons.warning_amber_rounded,
          color: AppColors.danger,
        ),
        _KpiCard(
          label: AppStrings.todayMovements,
          value: '—',
          icon:  Icons.swap_horiz_rounded,
          color: AppColors.success,
        ),
        _KpiCard(
          label: AppStrings.inventoryValue,
          value: '—',
          icon:  Icons.attach_money_rounded,
          color: AppColors.accent,
        ),
      ],
    );
  }

  Widget _buildQuickActions(BuildContext context, UserModel user) {
    final width = (MediaQuery.of(context).size.width - 44) / 2;
    return Wrap(
      spacing:    12,
      runSpacing: 12,
      children: [
        _QuickAction(
          icon:  Icons.add_circle_outline_rounded,
          label: 'Registrar\nIngreso',
          color: AppColors.success,
          width: width,
          onTap: () {},
        ),
        _QuickAction(
          icon:  Icons.remove_circle_outline_rounded,
          label: 'Registrar\nSalida',
          color: AppColors.warning,
          width: width,
          onTap: () {},
        ),
        _QuickAction(
          icon:  Icons.qr_code_scanner_rounded,
          label: 'Escanear\nProducto',
          color: AppColors.primary,
          width: width,
          onTap: () {},
        ),
        if (user.isSupervisor)
          _QuickAction(
            icon:  Icons.bar_chart_rounded,
            label: 'Ver\nReportes',
            color: AppColors.accent,
            width: width,
            onTap: () {},
          ),
      ],
    );
  }

  Widget _buildRecentActivity() {
    return Container(
      decoration: BoxDecoration(
        color:        AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color:     Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset:    const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: List.generate(3, (i) {
          return Column(
            children: [
              ListTile(
                leading: CircleAvatar(
                  backgroundColor: [
                    AppColors.successLight,
                    AppColors.warningLight,
                    AppColors.infoLight,
                  ][i],
                  child: Icon(
                    [
                      Icons.arrow_downward_rounded,
                      Icons.arrow_upward_rounded,
                      Icons.inventory_rounded,
                    ][i],
                    color: [
                      AppColors.success,
                      AppColors.warning,
                      AppColors.info,
                    ][i],
                    size: 20,
                  ),
                ),
                title: Text(
                  ['Ingreso registrado', 'Salida registrada', 'Producto actualizado'][i],
                  style: const TextStyle(
                    fontSize:   14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                subtitle: const Text(
                  'Conectando con el servidor...',
                  style: TextStyle(fontSize: 12, color: AppColors.textHint),
                ),
                trailing: const Text(
                  '—',
                  style: TextStyle(
                    fontSize: 12,
                    color:    AppColors.textSecondary,
                  ),
                ),
              ),
              if (i < 2) const Divider(height: 1, indent: 16, endIndent: 16),
            ],
          );
        }),
      ),
    );
  }
}


class _GreetingCard extends StatelessWidget {
  final UserModel user;
  const _GreetingCard({required this.user});

  String get _greeting {
    final h = DateTime.now().hour;
    if (h < 12) return 'Buenos días';
    if (h < 18) return 'Buenas tardes';
    return 'Buenas noches';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.accent],
          begin:  Alignment.topLeft,
          end:    Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color:     AppColors.primary.withOpacity(0.35),
            blurRadius: 16,
            offset:    const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        children: [
          // Avatar
          CircleAvatar(
            backgroundColor: Colors.white,
            radius:          28,
            child: Text(
              user.initials,
              style: TextStyle(
                color:      user.roleColor,
                fontSize:   20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 14),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$_greeting,',
                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                ),
                Text(
                  user.fullName,
                  style: const TextStyle(
                    color:      Colors.white,
                    fontSize:   16,
                    fontWeight: FontWeight.bold,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                RoleBadge(user: user),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _KpiCard extends StatelessWidget {
  final String   label;
  final String   value;
  final IconData icon;
  final Color    color;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color:        AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color:     Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset:    const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding:      const EdgeInsets.all(8),
            decoration:   BoxDecoration(
              color:        color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 22),
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              fontSize:   24,
              fontWeight: FontWeight.bold,
              color:      color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color:    AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String   label;
  final Color    color;
  final double   width;
  final VoidCallback onTap;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.color,
    required this.width,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap:        onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width:   width,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
        decoration: BoxDecoration(
          color:        AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
              color:     Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset:    const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding:    const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color:        color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize:   12,
                  fontWeight: FontWeight.w600,
                  color:      AppColors.textPrimary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DrawerItem extends StatelessWidget {
  final IconData icon;
  final String   label;
  final VoidCallback onTap;
  final Color    color;
  final bool     isActive;

  const _DrawerItem({
    required this.icon,
    required this.label,
    required this.onTap,
    this.color    = AppColors.textPrimary,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color:        isActive ? AppColors.primary.withOpacity(0.1) : null,
        borderRadius: BorderRadius.circular(10),
      ),
      child: ListTile(
        leading: Icon(
          icon,
          color: isActive ? AppColors.primary : color,
          size:  22,
        ),
        title: Text(
          label,
          style: TextStyle(
            color:      isActive ? AppColors.primary : color,
            fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
            fontSize:   14,
          ),
        ),
        onTap:   onTap,
        dense:   true,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
      ),
    );
  }
}

class _ModulesBanner extends StatelessWidget {
  const _ModulesBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color:        AppColors.infoLight,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.info.withOpacity(0.3)),
      ),
      child: const Row(
        children: [
          Icon(Icons.rocket_launch_rounded, color: AppColors.info, size: 20),
          SizedBox(width: 12),
          Expanded(
            child: Text(
              'Módulos de Productos, Movimientos, Alertas y Reportes se habilitarán conforme avancen los sprints del equipo.',
              style: TextStyle(fontSize: 12, color: AppColors.info),
            ),
          ),
        ],
      ),
    );
  }
}
