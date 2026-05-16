import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class BatchModel {
  final String batchCode;
  final int stock;
  final String expirationDate;

  BatchModel({
    required this.batchCode,
    required this.stock,
    required this.expirationDate,
  });

  factory BatchModel.fromJson(Map<String, dynamic> json) {
    return BatchModel(
      batchCode: json['batch_code'] ?? json['code'] ?? 'LOTE-UNK',
      stock: ProductModel._forceInt(json['stock'] ?? json['quantity']),
      expirationDate: json['expiration_date'] ?? json['expiry_date'] ?? 'S/V',
    );
  }

  bool get isExpired {
    try {
      final expiry = DateTime.parse(expirationDate);
      return expiry.isBefore(DateTime.now());
    } catch (_) {
      return false;
    }
  }
}

class ProductModel {
  final int id;
  final String code;
  final String name;
  final String category;
  final int currentStock;
  final int minStock;
  final String location;
  final List<BatchModel> batches;

  ProductModel({
    required this.id,
    required this.code,
    required this.name,
    required this.category,
    required this.currentStock,
    required this.minStock,
    required this.location,
    required this.batches,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    // 1. Mapeo ultra seguro de lotes
    var list = json['batches'] as List? ?? [];
    List<BatchModel> batchList = list.map((i) => BatchModel.fromJson(i)).toList();

    // 2. Extracción ultra segura de la categoría
    String categoryName = 'General';
    if (json['category'] != null && json['category']['name'] != null) {
      categoryName = json['category']['name'].toString();
    }

    // 3. Procesamiento y limpieza con nuestra función destructora de errores
    int parsedId = _forceInt(json['id']);
    int parsedCurrentStock = _forceInt(json['current_stock']);
    int parsedMinStock = _forceInt(json['min_stock']);

    return ProductModel(
      id: parsedId,
      code: json['code']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      category: categoryName,
      currentStock: parsedCurrentStock,
      minStock: parsedMinStock,
      location: json['location']?.toString() ?? 'No asignada',
      batches: batchList,
    );
  }

  // 🔥 ESTA FUNCIÓN ES LA QUE CURA EL ERROR DEFINITIVAMENTE:
  // Convierte CUALQUIER COSA (String raro, Double, Int, null) en un 'int' válido para Flutter.
  static int _forceInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    
    try {
      // Convertimos a string ("50.00" o "0000000055.000")
      String rawStr = value.toString().trim();
      
      // Si contiene un punto decimal, cortamos todo lo que esté después del punto
      if (rawStr.contains('.')) {
        rawStr = rawStr.split('.').first;
      }
      
      // Intentamos parsear el número limpio
      return int.tryParse(rawStr) ?? 0;
    } catch (_) {
      return 0; // Si pasa algo rarísimo, devuelve 0 en vez de romper la app
    }
  }

  bool get isStockCritical => currentStock <= minStock;
  Color get stockColor => isStockCritical ? AppColors.danger : AppColors.success;
}