class ApiConstants {
  ApiConstants._();

  // static const String baseUrl = 'http://10.0.2.2:8000/api';  // Android emulator
  static const String baseUrl = 'http://localhost:8000/api'; // ← ACTIVA ESTA
  // static const String baseUrl = 'http://192.168.1.100:8000/api'; // Dispositivo físico

  static const String login = '/auth/login';
  static const String me = '/auth/me';
  static const String users = '/users';
  static const String products = '/products';
  static const String categories = '/categories';
  static const String movements = '/movements';
  static const String alerts = '/alerts';
  static const String suppliers = '/suppliers';
  static const String clients = '/clients';

  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 15);

  static const String dashboard = "$baseUrl/dashboard";
}
