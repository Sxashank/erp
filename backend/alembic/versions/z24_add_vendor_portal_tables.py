"""Add vendor portal tables.

Revision ID: z24_add_vendor_portal_tables
Revises: z23_add_ess_portal_tables
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'z24_add_vendor_portal_tables'
down_revision: Union[str, None] = 'z23_add_ess_portal_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    vendor_portal_user_status = postgresql.ENUM(
        'PENDING_ACTIVATION', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED',
        name='vendorportaluserstatus', create_type=False
    )
    vendor_otp_purpose = postgresql.ENUM(
        'LOGIN', 'PASSWORD_RESET', 'EMAIL_VERIFICATION', 'PHONE_VERIFICATION', 'REGISTRATION',
        name='vendorotppurpose', create_type=False
    )
    business_type = postgresql.ENUM(
        'PROPRIETORSHIP', 'PARTNERSHIP', 'LLP', 'PRIVATE_LIMITED', 'PUBLIC_LIMITED',
        'GOVERNMENT', 'TRUST', 'SOCIETY', 'OTHERS',
        name='businesstype', create_type=False
    )
    registration_status = postgresql.ENUM(
        'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED',
        'APPROVED', 'REJECTED',
        name='registrationstatus', create_type=False
    )
    registration_document_type = postgresql.ENUM(
        'PAN_CARD', 'GST_CERTIFICATE', 'INCORPORATION_CERT', 'CANCELLED_CHEQUE',
        'MSME_CERTIFICATE', 'ADDRESS_PROOF', 'TRADE_LICENSE', 'OTHER',
        name='registrationdocumenttype', create_type=False
    )
    po_acknowledgement_status = postgresql.ENUM(
        'PENDING', 'ACKNOWLEDGED', 'REJECTED', 'CHANGE_REQUESTED', 'EXPIRED',
        name='poacknowledgementstatus', create_type=False
    )
    po_change_request_type = postgresql.ENUM(
        'QUANTITY_CHANGE', 'DELIVERY_DATE_CHANGE', 'PRICE_CHANGE',
        'ITEM_SUBSTITUTION', 'CANCELLATION', 'OTHER',
        name='pochangerequesttype', create_type=False
    )
    po_change_request_status = postgresql.ENUM(
        'PENDING', 'APPROVED', 'REJECTED', 'PARTIALLY_APPROVED', 'CANCELLED',
        name='pochangerequeststatus', create_type=False
    )
    vendor_invoice_status = postgresql.ENUM(
        'DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'MATCHED', 'EXCEPTION',
        'APPROVED', 'REJECTED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED',
        name='vendorinvoicestatus', create_type=False
    )
    invoice_matching_type = postgresql.ENUM(
        'TWO_WAY', 'THREE_WAY',
        name='invoicematchingtype', create_type=False
    )
    invoice_matching_status = postgresql.ENUM(
        'PENDING', 'MATCHED', 'PARTIAL_MATCH', 'MISMATCH',
        name='invoicematchingstatus', create_type=False
    )
    invoice_document_type = postgresql.ENUM(
        'INVOICE_PDF', 'DELIVERY_CHALLAN', 'GRN_COPY', 'PO_COPY',
        'E_WAY_BILL', 'OTHER',
        name='invoicedocumenttype', create_type=False
    )
    asn_status = postgresql.ENUM(
        'DRAFT', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'PARTIALLY_RECEIVED', 'CANCELLED',
        name='asnstatus', create_type=False
    )
    compliance_document_type = postgresql.ENUM(
        'PAN_CARD', 'GST_CERTIFICATE', 'MSME_CERTIFICATE', 'ISO_CERTIFICATE',
        'TDS_CERTIFICATE', 'FORM_16A', 'INSURANCE_POLICY', 'FSSAI_LICENSE',
        'POLLUTION_CERT', 'FACTORY_LICENSE', 'DRUG_LICENSE', 'CANCELLED_CHEQUE', 'OTHER',
        name='compliancedocumenttype', create_type=False
    )
    verification_status = postgresql.ENUM(
        'PENDING', 'VERIFIED', 'REJECTED',
        name='verificationstatus', create_type=False
    )
    notification_category = postgresql.ENUM(
        'PO', 'INVOICE', 'PAYMENT', 'ASN', 'COMPLIANCE', 'REGISTRATION', 'GENERAL',
        name='notificationcategory', create_type=False
    )
    notification_priority = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
        name='notificationpriority', create_type=False
    )

    # Create enums
    op.execute("CREATE TYPE vendorportaluserstatus AS ENUM ('PENDING_ACTIVATION', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED')")
    op.execute("CREATE TYPE vendorotppurpose AS ENUM ('LOGIN', 'PASSWORD_RESET', 'EMAIL_VERIFICATION', 'PHONE_VERIFICATION', 'REGISTRATION')")
    op.execute("CREATE TYPE businesstype AS ENUM ('PROPRIETORSHIP', 'PARTNERSHIP', 'LLP', 'PRIVATE_LIMITED', 'PUBLIC_LIMITED', 'GOVERNMENT', 'TRUST', 'SOCIETY', 'OTHERS')")
    op.execute("CREATE TYPE registrationstatus AS ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED', 'APPROVED', 'REJECTED')")
    op.execute("CREATE TYPE registrationdocumenttype AS ENUM ('PAN_CARD', 'GST_CERTIFICATE', 'INCORPORATION_CERT', 'CANCELLED_CHEQUE', 'MSME_CERTIFICATE', 'ADDRESS_PROOF', 'TRADE_LICENSE', 'OTHER')")
    op.execute("CREATE TYPE poacknowledgementstatus AS ENUM ('PENDING', 'ACKNOWLEDGED', 'REJECTED', 'CHANGE_REQUESTED', 'EXPIRED')")
    op.execute("CREATE TYPE pochangerequesttype AS ENUM ('QUANTITY_CHANGE', 'DELIVERY_DATE_CHANGE', 'PRICE_CHANGE', 'ITEM_SUBSTITUTION', 'CANCELLATION', 'OTHER')")
    op.execute("CREATE TYPE pochangerequeststatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'PARTIALLY_APPROVED', 'CANCELLED')")
    op.execute("CREATE TYPE vendorinvoicestatus AS ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'MATCHED', 'EXCEPTION', 'APPROVED', 'REJECTED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED')")
    op.execute("CREATE TYPE invoicematchingtype AS ENUM ('TWO_WAY', 'THREE_WAY')")
    op.execute("CREATE TYPE invoicematchingstatus AS ENUM ('PENDING', 'MATCHED', 'PARTIAL_MATCH', 'MISMATCH')")
    op.execute("CREATE TYPE invoicedocumenttype AS ENUM ('INVOICE_PDF', 'DELIVERY_CHALLAN', 'GRN_COPY', 'PO_COPY', 'E_WAY_BILL', 'OTHER')")
    op.execute("CREATE TYPE asnstatus AS ENUM ('DRAFT', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'PARTIALLY_RECEIVED', 'CANCELLED')")
    op.execute("CREATE TYPE compliancedocumenttype AS ENUM ('PAN_CARD', 'GST_CERTIFICATE', 'MSME_CERTIFICATE', 'ISO_CERTIFICATE', 'TDS_CERTIFICATE', 'FORM_16A', 'INSURANCE_POLICY', 'FSSAI_LICENSE', 'POLLUTION_CERT', 'FACTORY_LICENSE', 'DRUG_LICENSE', 'CANCELLED_CHEQUE', 'OTHER')")
    op.execute("CREATE TYPE verificationstatus AS ENUM ('PENDING', 'VERIFIED', 'REJECTED')")
    op.execute("CREATE TYPE notificationcategory AS ENUM ('PO', 'INVOICE', 'PAYMENT', 'ASN', 'COMPLIANCE', 'REGISTRATION', 'GENERAL')")
    op.execute("CREATE TYPE notificationpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")

    # 1. Portal Vendor User
    op.create_table(
        'portal_vendor_user',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),

        # Authentication
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),

        # Profile
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('designation', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),

        # Status
        sa.Column('is_primary_contact', sa.Boolean, default=False),
        sa.Column('email_verified', sa.Boolean, default=False),
        sa.Column('phone_verified', sa.Boolean, default=False),
        sa.Column('status', postgresql.ENUM('PENDING_ACTIVATION', 'ACTIVE', 'SUSPENDED', 'DEACTIVATED', name='vendorportaluserstatus', create_type=False), nullable=False),

        # Permissions
        sa.Column('can_view_pos', sa.Boolean, default=True),
        sa.Column('can_acknowledge_pos', sa.Boolean, default=True),
        sa.Column('can_submit_invoices', sa.Boolean, default=True),
        sa.Column('can_create_asn', sa.Boolean, default=True),
        sa.Column('can_view_payments', sa.Boolean, default=True),
        sa.Column('can_manage_users', sa.Boolean, default=False),
        sa.Column('can_manage_compliance', sa.Boolean, default=False),

        # Security
        sa.Column('failed_login_attempts', sa.Integer, default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('last_device_type', sa.String(50), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),

        # Invitation
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivation_reason', sa.String(500), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_vendor_user_vendor_id', 'portal_vendor_user', ['vendor_id'])
    op.create_index('ix_portal_vendor_user_email', 'portal_vendor_user', ['email'])
    op.create_index('ix_portal_vendor_user_organization_id', 'portal_vendor_user', ['organization_id'])

    # 2. Portal Vendor Session
    op.create_table(
        'portal_vendor_session',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=False),
        sa.Column('session_token', sa.String(512), nullable=False, unique=True),
        sa.Column('refresh_token', sa.String(512), nullable=True, unique=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_valid', sa.Boolean, default=True),
        sa.Column('invalidated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invalidation_reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_portal_vendor_session_user_id', 'portal_vendor_session', ['user_id'])
    op.create_index('ix_portal_vendor_session_session_token', 'portal_vendor_session', ['session_token'])

    # 3. Portal Vendor OTP
    op.create_table(
        'portal_vendor_otp',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('otp_code', sa.String(10), nullable=False),
        sa.Column('otp_hash', sa.String(64), nullable=False),
        sa.Column('purpose', postgresql.ENUM('LOGIN', 'PASSWORD_RESET', 'EMAIL_VERIFICATION', 'PHONE_VERIFICATION', 'REGISTRATION', name='vendorotppurpose', create_type=False), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer, default=0),
        sa.Column('max_attempts', sa.Integer, default=3),
        sa.Column('is_used', sa.Boolean, default=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_portal_vendor_otp_email_purpose', 'portal_vendor_otp', ['email', 'purpose'])

    # 4. Vendor Registration
    op.create_table(
        'portal_vendor_registration',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('registration_number', sa.String(50), nullable=False, unique=True),

        # Company Info
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255), nullable=True),
        sa.Column('business_type', postgresql.ENUM('PROPRIETORSHIP', 'PARTNERSHIP', 'LLP', 'PRIVATE_LIMITED', 'PUBLIC_LIMITED', 'GOVERNMENT', 'TRUST', 'SOCIETY', 'OTHERS', name='businesstype', create_type=False), nullable=False),
        sa.Column('incorporation_date', sa.Date, nullable=True),

        # Tax Info
        sa.Column('pan', sa.String(10), nullable=False),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('cin', sa.String(21), nullable=True),
        sa.Column('msme_number', sa.String(50), nullable=True),
        sa.Column('msme_category', sa.String(20), nullable=True),

        # Address
        sa.Column('registered_address', sa.Text, nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state_code', sa.String(2), nullable=False),
        sa.Column('pincode', sa.String(6), nullable=False),
        sa.Column('country', sa.String(50), default='India'),

        # Contact
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=False),
        sa.Column('contact_designation', sa.String(100), nullable=True),

        # Bank
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('account_number', sa.String(20), nullable=True),
        sa.Column('ifsc_code', sa.String(11), nullable=True),

        # Products
        sa.Column('product_categories', postgresql.JSONB, nullable=True),
        sa.Column('product_description', sa.Text, nullable=True),

        # Terms
        sa.Column('terms_accepted', sa.Boolean, default=False),
        sa.Column('terms_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('terms_version', sa.String(10), nullable=True),

        # Workflow
        sa.Column('status', postgresql.ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'ADDITIONAL_INFO_REQUIRED', 'APPROVED', 'REJECTED', name='registrationstatus', create_type=False), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_remarks', sa.Text, nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('rejection_category', sa.String(50), nullable=True),

        # Additional Info
        sa.Column('additional_info_request', sa.Text, nullable=True),
        sa.Column('additional_info_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('additional_info_response', sa.Text, nullable=True),
        sa.Column('additional_info_responded_at', sa.DateTime(timezone=True), nullable=True),

        # Link to created vendor
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=True),
        sa.Column('portal_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_vendor_registration_organization_id', 'portal_vendor_registration', ['organization_id'])
    op.create_index('ix_portal_vendor_registration_pan', 'portal_vendor_registration', ['pan'])
    op.create_index('ix_portal_vendor_registration_status', 'portal_vendor_registration', ['status'])

    # 5. Vendor Registration Document
    op.create_table(
        'portal_vendor_reg_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('registration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_registration.id'), nullable=False),
        sa.Column('document_type', postgresql.ENUM('PAN_CARD', 'GST_CERTIFICATE', 'INCORPORATION_CERT', 'CANCELLED_CHEQUE', 'MSME_CERTIFICATE', 'ADDRESS_PROOF', 'TRADE_LICENSE', 'OTHER', name='registrationdocumenttype', create_type=False), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('issue_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=True),

        # Verification
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_remarks', sa.Text, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_vendor_reg_document_registration_id', 'portal_vendor_reg_document', ['registration_id'])

    # 6. PO Acknowledgement
    op.create_table(
        'portal_po_acknowledgement',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('acknowledged_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=True),

        sa.Column('status', postgresql.ENUM('PENDING', 'ACKNOWLEDGED', 'REJECTED', 'CHANGE_REQUESTED', 'EXPIRED', name='poacknowledgementstatus', create_type=False), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('committed_delivery_date', sa.Date, nullable=True),
        sa.Column('delivery_remarks', sa.Text, nullable=True),

        # Rejection
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Change Request
        sa.Column('change_request_id', postgresql.UUID(as_uuid=True), nullable=True),

        # History
        sa.Column('response_history', postgresql.JSONB, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_po_acknowledgement_po_id', 'portal_po_acknowledgement', ['purchase_order_id'])
    op.create_index('ix_portal_po_acknowledgement_vendor_id', 'portal_po_acknowledgement', ['vendor_id'])

    # 7. PO Change Request
    op.create_table(
        'portal_po_change_request',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('requested_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=False),

        sa.Column('request_type', postgresql.ENUM('QUANTITY_CHANGE', 'DELIVERY_DATE_CHANGE', 'PRICE_CHANGE', 'ITEM_SUBSTITUTION', 'CANCELLATION', 'OTHER', name='pochangerequesttype', create_type=False), nullable=False),
        sa.Column('request_details', sa.Text, nullable=False),
        sa.Column('line_changes', postgresql.JSONB, nullable=True),
        sa.Column('justification', sa.Text, nullable=True),

        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'PARTIALLY_APPROVED', 'CANCELLED', name='pochangerequeststatus', create_type=False), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),

        # Review
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_remarks', sa.Text, nullable=True),

        # Cancellation
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_po_change_request_po_id', 'portal_po_change_request', ['purchase_order_id'])
    op.create_index('ix_portal_po_change_request_vendor_id', 'portal_po_change_request', ['vendor_id'])

    # 8. Vendor Invoice
    op.create_table(
        'portal_vendor_invoice',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('submitted_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=False),

        # References
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('grn_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Invoice Info
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('invoice_date', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('vendor_gstin', sa.String(15), nullable=True),
        sa.Column('place_of_supply', sa.String(2), nullable=True),

        # Amounts
        sa.Column('subtotal', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('taxable_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('cgst_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('sgst_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('igst_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('cess_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('tds_applicable', sa.Boolean, default=False),
        sa.Column('tds_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('tds_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('round_off', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('payable_amount', sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column('balance_amount', sa.Numeric(18, 2), nullable=True),

        sa.Column('is_igst_applicable', sa.Boolean, default=False),

        # Matching
        sa.Column('matching_type', postgresql.ENUM('TWO_WAY', 'THREE_WAY', name='invoicematchingtype', create_type=False), nullable=False, default='TWO_WAY'),
        sa.Column('matching_status', postgresql.ENUM('PENDING', 'MATCHED', 'PARTIAL_MATCH', 'MISMATCH', name='invoicematchingstatus', create_type=False), nullable=True),
        sa.Column('po_matched', sa.Boolean, default=False),
        sa.Column('grn_matched', sa.Boolean, default=False),
        sa.Column('matching_remarks', sa.Text, nullable=True),
        sa.Column('matching_exceptions', postgresql.JSONB, nullable=True),
        sa.Column('price_tolerance', sa.Numeric(5, 2), nullable=True),
        sa.Column('quantity_tolerance', sa.Numeric(5, 2), nullable=True),

        # Workflow
        sa.Column('status', postgresql.ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'MATCHED', 'EXCEPTION', 'APPROVED', 'REJECTED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED', name='vendorinvoicestatus', create_type=False), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_remarks', sa.Text, nullable=True),
        sa.Column('rejected_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),

        # Link to purchase bill
        sa.Column('purchase_bill_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_vendor_invoice_vendor_id', 'portal_vendor_invoice', ['vendor_id'])
    op.create_index('ix_portal_vendor_invoice_organization_id', 'portal_vendor_invoice', ['organization_id'])
    op.create_index('ix_portal_vendor_invoice_invoice_number', 'portal_vendor_invoice', ['invoice_number'])
    op.create_index('ix_portal_vendor_invoice_status', 'portal_vendor_invoice', ['status'])

    # 9. Vendor Invoice Line
    op.create_table(
        'portal_vendor_invoice_line',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_invoice.id'), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),

        # PO Reference
        sa.Column('po_line_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('po_line_number', sa.Integer, nullable=True),
        sa.Column('grn_line_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Item
        sa.Column('item_code', sa.String(50), nullable=True),
        sa.Column('item_description', sa.Text, nullable=False),
        sa.Column('hsn_sac_code', sa.String(8), nullable=True),
        sa.Column('uom', sa.String(20), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('line_total', sa.Numeric(18, 2), nullable=False),

        # Discount
        sa.Column('discount_percent', sa.Numeric(5, 2), default=0),
        sa.Column('discount_amount', sa.Numeric(18, 2), default=0),
        sa.Column('taxable_amount', sa.Numeric(18, 2), nullable=False),

        # GST
        sa.Column('cgst_rate', sa.Numeric(5, 2), default=0),
        sa.Column('cgst_amount', sa.Numeric(18, 2), default=0),
        sa.Column('sgst_rate', sa.Numeric(5, 2), default=0),
        sa.Column('sgst_amount', sa.Numeric(18, 2), default=0),
        sa.Column('igst_rate', sa.Numeric(5, 2), default=0),
        sa.Column('igst_amount', sa.Numeric(18, 2), default=0),
        sa.Column('cess_rate', sa.Numeric(5, 2), default=0),
        sa.Column('cess_amount', sa.Numeric(18, 2), default=0),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=False),

        # Matching Variance
        sa.Column('po_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('po_unit_price', sa.Numeric(18, 4), nullable=True),
        sa.Column('grn_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('quantity_variance', sa.Numeric(18, 4), nullable=True),
        sa.Column('price_variance', sa.Numeric(18, 4), nullable=True),
        sa.Column('variance_amount', sa.Numeric(18, 2), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_vendor_invoice_line_invoice_id', 'portal_vendor_invoice_line', ['invoice_id'])

    # 10. Vendor Invoice Document
    op.create_table(
        'portal_vendor_invoice_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_invoice.id'), nullable=False),
        sa.Column('document_type', postgresql.ENUM('INVOICE_PDF', 'DELIVERY_CHALLAN', 'GRN_COPY', 'PO_COPY', 'E_WAY_BILL', 'OTHER', name='invoicedocumenttype', create_type=False), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('document_date', sa.Date, nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_vendor_invoice_document_invoice_id', 'portal_vendor_invoice_document', ['invoice_id'])

    # 11. Advanced Shipping Notice (ASN)
    op.create_table(
        'portal_asn',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=False),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('asn_number', sa.String(50), nullable=False, unique=True),

        # Shipment Info
        sa.Column('ship_date', sa.Date, nullable=True),
        sa.Column('expected_delivery_date', sa.Date, nullable=True),
        sa.Column('actual_delivery_date', sa.Date, nullable=True),
        sa.Column('carrier_name', sa.String(100), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('vehicle_number', sa.String(20), nullable=True),
        sa.Column('driver_name', sa.String(100), nullable=True),
        sa.Column('driver_phone', sa.String(20), nullable=True),

        # Packaging
        sa.Column('total_packages', sa.Integer, nullable=True),
        sa.Column('total_weight', sa.Numeric(18, 4), nullable=True),
        sa.Column('weight_uom', sa.String(10), nullable=True),

        # Status
        sa.Column('status', postgresql.ENUM('DRAFT', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'PARTIALLY_RECEIVED', 'CANCELLED', name='asnstatus', create_type=False), nullable=False),
        sa.Column('dispatched_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_remarks', sa.Text, nullable=True),

        # Cancellation
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_asn_vendor_id', 'portal_asn', ['vendor_id'])
    op.create_index('ix_portal_asn_organization_id', 'portal_asn', ['organization_id'])
    op.create_index('ix_portal_asn_po_id', 'portal_asn', ['purchase_order_id'])
    op.create_index('ix_portal_asn_status', 'portal_asn', ['status'])

    # 12. ASN Line
    op.create_table(
        'portal_asn_line',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('asn_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_asn.id'), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('po_line_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Item
        sa.Column('item_code', sa.String(50), nullable=True),
        sa.Column('item_description', sa.Text, nullable=False),
        sa.Column('shipped_quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('uom', sa.String(20), nullable=True),

        # Batch/Serial
        sa.Column('batch_number', sa.String(50), nullable=True),
        sa.Column('serial_numbers', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('manufacturing_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),

        # Packaging
        sa.Column('package_number', sa.String(50), nullable=True),
        sa.Column('weight', sa.Numeric(18, 4), nullable=True),

        # Received (filled by buyer)
        sa.Column('received_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_by_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_asn_line_asn_id', 'portal_asn_line', ['asn_id'])

    # 13. Compliance Document
    op.create_table(
        'portal_compliance_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=False),

        sa.Column('document_type', postgresql.ENUM('PAN_CARD', 'GST_CERTIFICATE', 'MSME_CERTIFICATE', 'ISO_CERTIFICATE', 'TDS_CERTIFICATE', 'FORM_16A', 'INSURANCE_POLICY', 'FSSAI_LICENSE', 'POLLUTION_CERT', 'FACTORY_LICENSE', 'DRUG_LICENSE', 'CANCELLED_CHEQUE', 'OTHER', name='compliancedocumenttype', create_type=False), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('document_number', sa.String(100), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=True),

        # Validity
        sa.Column('issue_date', sa.Date, nullable=True),
        sa.Column('expiry_date', sa.Date, nullable=True),
        sa.Column('is_perpetual', sa.Boolean, default=False),
        sa.Column('is_expired', sa.Boolean, default=False),
        sa.Column('days_to_expiry', sa.Integer, nullable=True),

        # Verification
        sa.Column('verification_status', postgresql.ENUM('PENDING', 'VERIFIED', 'REJECTED', name='verificationstatus', create_type=False), nullable=True),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_remarks', sa.Text, nullable=True),

        # Alerts
        sa.Column('expiry_alert_sent', sa.Boolean, default=False),
        sa.Column('expiry_alert_sent_at', sa.DateTime(timezone=True), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, default=1),
    )
    op.create_index('ix_portal_compliance_document_vendor_id', 'portal_compliance_document', ['vendor_id'])
    op.create_index('ix_portal_compliance_document_organization_id', 'portal_compliance_document', ['organization_id'])
    op.create_index('ix_portal_compliance_document_type', 'portal_compliance_document', ['document_type'])
    op.create_index('ix_portal_compliance_document_expiry', 'portal_compliance_document', ['expiry_date'])

    # 14. Vendor Notification
    op.create_table(
        'portal_vendor_notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_vendor.id'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mst_organization.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_vendor_user.id'), nullable=True),

        sa.Column('category', postgresql.ENUM('PO', 'INVOICE', 'PAYMENT', 'ASN', 'COMPLIANCE', 'REGISTRATION', 'GENERAL', name='notificationcategory', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='notificationpriority', create_type=False), nullable=False, default='MEDIUM'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),

        # Reference
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),

        # Status
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_by_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_vendor_notification_vendor_id', 'portal_vendor_notification', ['vendor_id'])
    op.create_index('ix_portal_vendor_notification_user_id', 'portal_vendor_notification', ['user_id'])
    op.create_index('ix_portal_vendor_notification_is_read', 'portal_vendor_notification', ['is_read'])
    op.create_index('ix_portal_vendor_notification_created_at', 'portal_vendor_notification', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('portal_vendor_notification')
    op.drop_table('portal_compliance_document')
    op.drop_table('portal_asn_line')
    op.drop_table('portal_asn')
    op.drop_table('portal_vendor_invoice_document')
    op.drop_table('portal_vendor_invoice_line')
    op.drop_table('portal_vendor_invoice')
    op.drop_table('portal_po_change_request')
    op.drop_table('portal_po_acknowledgement')
    op.drop_table('portal_vendor_reg_document')
    op.drop_table('portal_vendor_registration')
    op.drop_table('portal_vendor_otp')
    op.drop_table('portal_vendor_session')
    op.drop_table('portal_vendor_user')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationcategory")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS compliancedocumenttype")
    op.execute("DROP TYPE IF EXISTS asnstatus")
    op.execute("DROP TYPE IF EXISTS invoicedocumenttype")
    op.execute("DROP TYPE IF EXISTS invoicematchingstatus")
    op.execute("DROP TYPE IF EXISTS invoicematchingtype")
    op.execute("DROP TYPE IF EXISTS vendorinvoicestatus")
    op.execute("DROP TYPE IF EXISTS pochangerequeststatus")
    op.execute("DROP TYPE IF EXISTS pochangerequesttype")
    op.execute("DROP TYPE IF EXISTS poacknowledgementstatus")
    op.execute("DROP TYPE IF EXISTS registrationdocumenttype")
    op.execute("DROP TYPE IF EXISTS registrationstatus")
    op.execute("DROP TYPE IF EXISTS businesstype")
    op.execute("DROP TYPE IF EXISTS vendorotppurpose")
    op.execute("DROP TYPE IF EXISTS vendorportaluserstatus")
