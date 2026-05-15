import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/constants/app_strings.dart';
import 'providers/auth_provider.dart';
import 'presentation/screens/splash/splash_screen.dart';
import 'presentation/screens/login/login_screen.dart';
import 'presentation/screens/dashboard/dashboard_screen.dart';

class MedStockApp extends StatelessWidget {
  const MedStockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title:                  AppStrings.appName,
      debugShowCheckedModeBanner: false,
      theme:                  AppTheme.lightTheme,
      home:                   const _AppNavigator(),
    );
  }
}

class _AppNavigator extends StatefulWidget {
  const _AppNavigator();

  @override
  State<_AppNavigator> createState() => _AppNavigatorState();
}

class _AppNavigatorState extends State<_AppNavigator> {
  @override
  void initState() {
    super.initState();
    // Verificar si hay sesión guardada en cuanto inicia la app
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().checkAuthStatus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        switch (auth.status) {
          case AuthStatus.unknown:
            // Verificando sesión → mostrar splash
            return const SplashScreen();
          case AuthStatus.authenticated:
            // Sesión válida → ir al dashboard
            return const DashboardScreen();
          case AuthStatus.unauthenticated:
            // Sin sesión → ir al login
            return const LoginScreen();
        }
      },
    );
  }
}
