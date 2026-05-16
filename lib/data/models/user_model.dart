import '../../core/constants/app_colors.dart';
import 'package:flutter/material.dart';

class UserModel {
  final int    id;
  final String username;
  final String email;
  final String fullName;
  final String role;
  final bool   isActive;
  final String? phone;

  const UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.fullName,
    required this.role,
    required this.isActive,
    this.phone,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id:       json['id'] as int,
      username: json['username'] as String,
      email:    json['email'] as String,
      fullName: json['full_name'] as String,
      role:     json['role'] as String,
      isActive: json['is_active'] as bool? ?? true,
      phone:    json['phone'] as String?,
    );
  }

  String get roleLabel {
    const labels = {
      'admin':      'Administrador',
      'supervisor': 'Supervisor',
      'almacenero': 'Almacenero',
    };
    return labels[role] ?? role;
  }

  String get initials {
    final parts = fullName.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return fullName.isNotEmpty ? fullName[0].toUpperCase() : 'U';
  }

  Color get roleColor {
    switch (role) {
      case 'admin':      return AppColors.adminColor;
      case 'supervisor': return AppColors.supervisorColor;
      default:           return AppColors.almaceneroColor;
    }
  }

  bool get isAdmin      => role == 'admin';
  bool get isSupervisor => role == 'supervisor' || isAdmin;
}

class AuthResponse {
  final String    accessToken;
  final String    tokenType;
  final UserModel user;

  const AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String,
      tokenType:   json['token_type'] as String,
      user:        UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}
