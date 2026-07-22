import frappe
from frappe import _

# New, additive-only endpoints for a logged-in user to manage/view their own
# profile details (currently just mobile_no). Deliberately kept in a
# standalone file — nothing in auth.py/ghost.py/otp.py is touched by this
# module, so the existing login/conversion/OTP flows are unaffected.


def _current_real_user_or_throw():
	"""
	Self-only identity guard: rejects Guest outright. Ghost users
	(frappe.session.user starting with "ghost_") are allowed through — a
	ghost session is still a real User record, and letting a ghost user set
	their own mobile_no ahead of conversion is harmless (the field carries
	over on convert_to_real_user's rename/migration either way).
	"""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)
	return user


@frappe.whitelist()
def update_mobile_number(mobile_no=None):
	"""
	Lets the logged-in caller set/update their own mobile_no. Self-only —
	always acts on frappe.session.user, never a caller-supplied user id.

	Required: mobile_no.

	Rejects if mobile_no is already in use by a *different* user (same
	uniqueness expectation ghost.api.auth.login already relies on when it
	looks a user up by mobile_no for phone-based login).

	Response:
	  {"success": true, "user", "mobile_no"}
	"""
	user = _current_real_user_or_throw()

	mobile_no = str(mobile_no or "").strip()
	if not mobile_no:
		frappe.throw(_("mobile_no is required"), frappe.ValidationError)

	existing_owner = frappe.db.get_value("User", {"mobile_no": mobile_no}, "name")
	if existing_owner and existing_owner != user:
		frappe.throw(
			_("This mobile number is already associated with another account."),
			frappe.ValidationError,
		)

	frappe.db.set_value("User", user, "mobile_no", mobile_no)
	frappe.db.commit()

	return {"success": True, "user": user, "mobile_no": mobile_no}


@frappe.whitelist()
def get_user_details():
	"""
	Returns the logged-in caller's own profile. Self-only — no user-id
	param, always resolved from frappe.session.user, so this can never be
	used to look up someone else's details.

	Response:
	  {"success": true, "name", "email", "mobile_no", "first_name",
	   "last_name", "full_name", "user_image"}
	"""
	user = _current_real_user_or_throw()

	doc = frappe.db.get_value(
		"User",
		user,
		["name", "email", "mobile_no", "first_name", "last_name", "full_name", "user_image"],
		as_dict=True,
	)

	return {"success": True, **doc}
