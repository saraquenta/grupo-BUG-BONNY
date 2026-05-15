import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const Color primary      = Color(0xFF1565C0);
  static const Color primaryLight = Color(0xFF42A5F5);
  static const Color primaryDark  = Color(0xFF0D47A1);

  static const Color accent       = Color(0xFF00ACC1);

  static const Color success      = Color(0xFF2E7D32);
  static const Color successLight = Color(0xFFE8F5E9);
  static const Color warning      = Color(0xFFF57C00);
  static const Color warningLight = Color(0xFFFFF3E0);
  static const Color danger       = Color(0xFFC62828);
  static const Color dangerLight  = Color(0xFFFFEBEE);
  static const Color info         = Color(0xFF0277BD);
  static const Color infoLight    = Color(0xFFE1F5FE);

  static const Color background   = Color(0xFFF5F7FA);
  static const Color surface      = Color(0xFFFFFFFF);
  static const Color textPrimary  = Color(0xFF1A1A2E);
  static const Color textSecondary= Color(0xFF6B7280);
  static const Color textHint     = Color(0xFF9CA3AF);
  static const Color border       = Color(0xFFE5E7EB);
  static const Color divider      = Color(0xFFF3F4F6);

  static const Color adminColor      = Color(0xFF7C3AED);
  static const Color supervisorColor = Color(0xFF0284C7);
  static const Color almaceneroColor = Color(0xFF059669);

  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary, accent],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
