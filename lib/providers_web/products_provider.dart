import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';
import '../../core/constants/api_constants.dart';

class WebProductsProvider extends ChangeNotifier {
  List<Map<String, dynamic>> products = [];
  List<Map<String, dynamic>> categories = [];

  // Filtros
  String? search;
  int? categoryId;
  bool? lowStock;

  // Estados
  bool isLoading = true;
  bool isCategoriesLoading = true;
  String? error;

  Future<void> loadProducts() async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      var endpoint = ApiConstants.products;
      final params = <String, dynamic>{};

      if (search != null && search!.isNotEmpty) params['search'] = search;
      if (categoryId != null) params['category_id'] = categoryId;
      if (lowStock != null) params['low_stock'] = lowStock;

      if (params.isNotEmpty) {
        endpoint +=
            '?${params.entries.map((e) => '${e.key}=${e.value}').join('&')}';
      }

      final data = await ApiService.get(endpoint);

      if (data['items'] != null) {
        products = List<Map<String, dynamic>>.from(data['items']);
      }

      isLoading = false;
      notifyListeners();
    } catch (e) {
      error = e.toString().replaceFirst('Exception: ', '');
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadCategories() async {
    isCategoriesLoading = true;
    notifyListeners();

    try {
      final data = await ApiService.get(ApiConstants.categories);

      if (data is List) {
        categories = List<Map<String, dynamic>>.from(data);
      }

      isCategoriesLoading = false;
      notifyListeners();
    } catch (e) {
      isCategoriesLoading = false;
      notifyListeners();
    }
  }

  void setFilters({
    String? search,
    int? categoryId,
    bool? lowStock,
  }) {
    this.search = search;
    this.categoryId = categoryId;
    this.lowStock = lowStock;
    loadProducts();
  }

  void clearFilters() {
    search = null;
    categoryId = null;
    lowStock = null;
    loadProducts();
  }

  Future<bool> createProduct(Map<String, dynamic> data) async {
    try {
      await ApiService.post(ApiConstants.products, data);
      await loadProducts();
      return true;
    } catch (e) {
      error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateProduct(int id, Map<String, dynamic> data) async {
    try {
      await ApiService.put('${ApiConstants.products}/$id', data);
      await loadProducts();
      return true;
    } catch (e) {
      error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> deleteProduct(int id) async {
    try {
      await ApiService.delete('${ApiConstants.products}/$id');
      await loadProducts();
      return true;
    } catch (e) {
      error = e.toString();
      notifyListeners();
      return false;
    }
  }
}
