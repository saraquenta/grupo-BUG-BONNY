import 'package:flutter/material.dart';
import '../data/models/user_model.dart';
import '../data/services/auth_service.dart';
import '../data/services/api_service.dart';
import '../data/services/storage_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthProvider extends ChangeNotifier {
  AuthStatus _status    = AuthStatus.unknown;
  UserModel? _user;
  String?    _errorMsg;
  bool       _isLoading = false;

  AuthStatus get status    => _status;
  UserModel? get user      => _user;
  String?    get errorMsg  => _errorMsg;
  bool       get isLoading => _isLoading;

  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isAdmin         => _user?.isAdmin ?? false;
  bool get isSupervisor    => _user?.isSupervisor ?? false;

  Future<void> checkAuthStatus() async {
    final hasToken = await StorageService.hasToken();

    if (!hasToken) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      final user = await AuthService.getMe();
      _user   = user;
      _status = AuthStatus.authenticated;
    } on ApiException {
      // Token inválido o expirado
      await StorageService.clearAll();
      _status = AuthStatus.unauthenticated;
    } catch (_) {
      await StorageService.clearAll();
      _status = AuthStatus.unauthenticated;
    }

    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _errorMsg  = null;
    notifyListeners();

    try {
      final response = await AuthService.login(username.trim(), password);

      await StorageService.saveToken(response.accessToken);
      await StorageService.saveUsername(username.trim());

      _user   = response.user;
      _status = AuthStatus.authenticated;
      return true;
    } on ApiException catch (e) {
      _errorMsg = e.message;
      _status   = AuthStatus.unauthenticated;
      return false;
    } catch (e) {
      _errorMsg = 'Error de conexión. Verifica que el servidor esté activo.';
      _status   = AuthStatus.unauthenticated;
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await StorageService.clearAll();
    _user     = null;
    _errorMsg = null;
    _status   = AuthStatus.unauthenticated;
    notifyListeners();
  }

  void clearError() {
    _errorMsg = null;
    notifyListeners();
  }
}
