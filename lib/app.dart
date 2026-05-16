import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'core/constants/app_strings.dart';
import 'providers/auth_provider.dart';
import 'providers_web/dashboard_provider.dart';
import 'providers_web/products_provider.dart';
import 'presentation/screens/splash/splash_screen.dart';
import 'presentation/screens/login/login_screen.dart';
import 'presentation/screens/dashboard/dashboard_screen.dart';
import 'presentation/screens/web/auth/login_screen.dart';
import 'presentation/screens/web/dashboard/dashboard_screen.dart';
import 'presentation/screens/web/products/products_screen.dart';

class MedStockApp extends StatelessWidget {
  const MedStockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => WebDashboardProvider()),
        ChangeNotifierProvider(create: (_) => WebProductsProvider()),
      ],
      child: MaterialApp(
        title: AppStrings.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        initialRoute: '/',
        routes: {
          '/': (context) => const _AppNavigator(),
          '/web/login': (context) => const WebLoginScreen(),
          '/web/dashboard': (context) => const WebDashboardScreen(),
          '/web/products': (context) => const WebProductsScreen(),
        },
      ),
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
            return const SplashScreen();
          case AuthStatus.authenticated:
            // Detectar si es web (ancho > 800)
            final isWeb = MediaQuery.of(context).size.width > 800;
            // Verificar si es admin (usando el método isAdmin del UserModel)
            final user =
                auth.user; // ✅ Usando auth.user en lugar de currentUser
            if (isWeb && user != null && user.isAdmin) {
              return const WebDashboardScreen();
            }
            return const DashboardScreen();
          case AuthStatus.unauthenticated:
            final isWeb = MediaQuery.of(context).size.width > 800;
            if (isWeb) {
              return const WebLoginScreen();
            }
            return const LoginScreen();
        }
      },
    );
  }
}
