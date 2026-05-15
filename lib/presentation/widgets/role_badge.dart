import 'package:flutter/material.dart';
import '../../data/models/user_model.dart';

class RoleBadge extends StatelessWidget {
  final UserModel user;
  const RoleBadge({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color:        user.roleColor.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: user.roleColor.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            user.isAdmin
                ? Icons.admin_panel_settings
                : user.isSupervisor
                    ? Icons.supervisor_account
                    : Icons.person,
            size:  13,
            color: user.roleColor,
          ),
          const SizedBox(width: 4),
          Text(
            user.roleLabel,
            style: TextStyle(
              fontSize:   12,
              fontWeight: FontWeight.w600,
              color:      user.roleColor,
            ),
          ),
        ],
      ),
    );
  }
}
