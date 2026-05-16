import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_strings.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double>   _fadeAnimation;
  late Animation<double>   _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync:    this,
      duration: const Duration(milliseconds: 1200),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
    _scaleAnimation = Tween<double>(begin: 0.7, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
    );
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [AppColors.primaryDark, AppColors.primary, AppColors.accent],
            begin:  Alignment.topLeft,
            end:    Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: FadeTransition(
            opacity: _fadeAnimation,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Logo animado
                ScaleTransition(
                  scale: _scaleAnimation,
                  child: Container(
                    width:  110,
                    height: 110,
                    decoration: BoxDecoration(
                      color:        Colors.white,
                      borderRadius: BorderRadius.circular(28),
                      boxShadow: [
                        BoxShadow(
                          color:   Colors.black.withOpacity(0.2),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.medical_services_rounded,
                      size:  64,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(height: 28),

                // Nombre de la app
                const Text(
                  AppStrings.appName,
                  style: TextStyle(
                    color:       Colors.white,
                    fontSize:    34,
                    fontWeight:  FontWeight.bold,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Gestión Inteligente de Inventario',
                  style: TextStyle(
                    color:    Colors.white70,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  AppStrings.company,
                  style: TextStyle(
                    color:      Colors.white54,
                    fontSize:   12,
                    fontStyle:  FontStyle.italic,
                  ),
                ),
                const SizedBox(height: 70),

                // Indicador de carga
                const SizedBox(
                  width:  36,
                  height: 36,
                  child: CircularProgressIndicator(
                    color:       Colors.white,
                    strokeWidth: 2.5,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Cargando...',
                  style: TextStyle(color: Colors.white60, fontSize: 13),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
