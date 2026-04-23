"""Add E-Invoice and E-Way Bill tables.

Revision ID: z21_add_einvoice_ewaybill_tables
Revises: z20_add_separation_fnf_tables
Create Date: 2026-01-15

Tables created:
- gst_einvoice_request: E-Invoice generation requests
- gst_eway_bill: E-Way Bill tracking
- gst_eway_bill_item: E-Way Bill line items
- gst_eway_bill_vehicle_update: Vehicle update history
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "z21_add_einvoice_ewaybill_tables"
down_revision: str = "z20_add_separation_fnf_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE einvoiceprovider AS ENUM ('NIC', 'CLEARTAX', 'TALLY', 'ZOHO');
        CREATE TYPE einvoicerequeststatus AS ENUM ('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', 'CANCELLED');
        CREATE TYPE ewaybillprovider AS ENUM ('NIC', 'CLEARTAX', 'MANUAL');
        CREATE TYPE ewaybillstatus AS ENUM ('DRAFT', 'GENERATED', 'ACTIVE', 'CANCELLED', 'EXPIRED', 'EXTENDED');
        CREATE TYPE transportmode AS ENUM ('1', '2', '3', '4');
        CREATE TYPE vehicletype AS ENUM ('R', 'O');
        CREATE TYPE transactiontype AS ENUM ('1', '2', '3', '4');
        CREATE TYPE subsupplytype AS ENUM ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12');
    """)

    # Create gst_einvoice_request table
    op.create_table(
        "gst_einvoice_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sales_invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Provider
        sa.Column("provider", sa.Enum('NIC', 'CLEARTAX', 'TALLY', 'ZOHO', name='einvoiceprovider', create_type=False), nullable=False, server_default='NIC'),
        # Request details
        sa.Column("request_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status", sa.Enum('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', 'CANCELLED', name='einvoicerequeststatus', create_type=False), nullable=False, server_default='PENDING'),
        # Generated values
        sa.Column("irn", sa.String(64), nullable=True, unique=True),
        sa.Column("ack_number", sa.String(50), nullable=True),
        sa.Column("ack_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_invoice", sa.Text(), nullable=True),
        sa.Column("signed_qr_code", sa.Text(), nullable=True),
        sa.Column("qr_code_image", sa.Text(), nullable=True),
        # E-Way Bill auto-generation
        sa.Column("eway_bill_auto_generated", sa.Boolean(), default=False, nullable=False),
        sa.Column("eway_bill_number", sa.String(20), nullable=True),
        sa.Column("eway_bill_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eway_bill_validity", sa.DateTime(timezone=True), nullable=True),
        # Request/Response
        sa.Column("request_payload", postgresql.JSONB(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        # Error handling
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSONB(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0, nullable=False),
        # Cancellation
        sa.Column("is_cancelled", sa.Boolean(), default=False, nullable=False),
        sa.Column("cancel_reason", sa.String(200), nullable=True),
        sa.Column("cancel_remarks", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        # User tracking
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"]),
        sa.ForeignKeyConstraint(["gst_registration_id"], ["mst_gst_registration.id"]),
        sa.ForeignKeyConstraint(["sales_invoice_id"], ["txn_sales_invoice.id"]),
        sa.ForeignKeyConstraint(["cancelled_by"], ["mst_user.id"]),
        sa.ForeignKeyConstraint(["initiated_by"], ["mst_user.id"]),
    )
    op.create_index("ix_einvoice_request_org_status", "gst_einvoice_request", ["organization_id", "status"])
    op.create_index("ix_einvoice_request_invoice", "gst_einvoice_request", ["sales_invoice_id"])
    op.create_index("ix_einvoice_request_irn", "gst_einvoice_request", ["irn"])

    # Create gst_eway_bill table
    op.create_table(
        "gst_eway_bill",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Linked documents
        sa.Column("sales_invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("einvoice_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Provider
        sa.Column("provider", sa.Enum('NIC', 'CLEARTAX', 'MANUAL', name='ewaybillprovider', create_type=False), nullable=False, server_default='NIC'),
        # E-Way Bill details
        sa.Column("eway_bill_number", sa.String(20), nullable=True, unique=True),
        sa.Column("eway_bill_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum('DRAFT', 'GENERATED', 'ACTIVE', 'CANCELLED', 'EXPIRED', 'EXTENDED', name='ewaybillstatus', create_type=False), nullable=False, server_default='DRAFT'),
        # Document reference
        sa.Column("document_type", sa.String(20), nullable=False, server_default='INV'),
        sa.Column("document_number", sa.String(50), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=False),
        # Transaction details
        sa.Column("transaction_type", sa.Enum('1', '2', '3', '4', name='transactiontype', create_type=False), nullable=False, server_default='1'),
        sa.Column("sub_supply_type", sa.Enum('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', name='subsupplytype', create_type=False), nullable=False, server_default='1'),
        # Supplier (From)
        sa.Column("supplier_gstin", sa.String(15), nullable=False),
        sa.Column("supplier_name", sa.String(200), nullable=False),
        sa.Column("supplier_address", sa.Text(), nullable=False),
        sa.Column("supplier_place", sa.String(100), nullable=False),
        sa.Column("supplier_pincode", sa.String(6), nullable=False),
        sa.Column("supplier_state_code", sa.String(2), nullable=False),
        # Recipient (To)
        sa.Column("recipient_gstin", sa.String(15), nullable=True),
        sa.Column("recipient_name", sa.String(200), nullable=False),
        sa.Column("recipient_address", sa.Text(), nullable=False),
        sa.Column("recipient_place", sa.String(100), nullable=False),
        sa.Column("recipient_pincode", sa.String(6), nullable=False),
        sa.Column("recipient_state_code", sa.String(2), nullable=False),
        # Dispatch details
        sa.Column("dispatch_from_gstin", sa.String(15), nullable=True),
        sa.Column("dispatch_from_name", sa.String(200), nullable=True),
        sa.Column("dispatch_from_address", sa.Text(), nullable=True),
        sa.Column("dispatch_from_place", sa.String(100), nullable=True),
        sa.Column("dispatch_from_pincode", sa.String(6), nullable=True),
        sa.Column("dispatch_from_state_code", sa.String(2), nullable=True),
        # Ship to details
        sa.Column("ship_to_gstin", sa.String(15), nullable=True),
        sa.Column("ship_to_name", sa.String(200), nullable=True),
        sa.Column("ship_to_address", sa.Text(), nullable=True),
        sa.Column("ship_to_place", sa.String(100), nullable=True),
        sa.Column("ship_to_pincode", sa.String(6), nullable=True),
        sa.Column("ship_to_state_code", sa.String(2), nullable=True),
        # Item summary
        sa.Column("total_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("hsn_code", sa.String(8), nullable=False),
        sa.Column("product_description", sa.String(200), nullable=False),
        # Value details
        sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column("sgst_amount", sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column("igst_amount", sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column("cess_amount", sa.Numeric(18, 2), nullable=False, server_default='0'),
        sa.Column("total_value", sa.Numeric(18, 2), nullable=False),
        # Transport details
        sa.Column("transport_mode", sa.Enum('1', '2', '3', '4', name='transportmode', create_type=False), nullable=False, server_default='1'),
        sa.Column("transporter_id", sa.String(15), nullable=True),
        sa.Column("transporter_name", sa.String(200), nullable=True),
        sa.Column("transport_doc_number", sa.String(50), nullable=True),
        sa.Column("transport_doc_date", sa.Date(), nullable=True),
        # Vehicle details
        sa.Column("vehicle_number", sa.String(20), nullable=True),
        sa.Column("vehicle_type", sa.Enum('R', 'O', name='vehicletype', create_type=False), nullable=True),
        # Distance
        sa.Column("approximate_distance", sa.Integer(), nullable=False, server_default='0'),
        # Extension tracking
        sa.Column("extension_count", sa.Integer(), nullable=False, server_default='0'),
        sa.Column("last_extended_at", sa.DateTime(timezone=True), nullable=True),
        # Cancellation
        sa.Column("is_cancelled", sa.Boolean(), default=False, nullable=False),
        sa.Column("cancel_reason_code", sa.String(10), nullable=True),
        sa.Column("cancel_remarks", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        # Request/Response
        sa.Column("request_payload", postgresql.JSONB(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # User tracking
        sa.Column("created_by_user", postgresql.UUID(as_uuid=True), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["mst_organization.id"]),
        sa.ForeignKeyConstraint(["gst_registration_id"], ["mst_gst_registration.id"]),
        sa.ForeignKeyConstraint(["sales_invoice_id"], ["txn_sales_invoice.id"]),
        sa.ForeignKeyConstraint(["einvoice_request_id"], ["gst_einvoice_request.id"]),
        sa.ForeignKeyConstraint(["cancelled_by"], ["mst_user.id"]),
        sa.ForeignKeyConstraint(["created_by_user"], ["mst_user.id"]),
    )
    op.create_index("ix_eway_bill_org_status", "gst_eway_bill", ["organization_id", "status"])
    op.create_index("ix_eway_bill_number", "gst_eway_bill", ["eway_bill_number"])
    op.create_index("ix_eway_bill_supplier", "gst_eway_bill", ["supplier_gstin"])
    op.create_index("ix_eway_bill_validity", "gst_eway_bill", ["valid_until"])

    # Create gst_eway_bill_item table
    op.create_table(
        "gst_eway_bill_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("eway_bill_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Item details
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("product_description", sa.String(500), nullable=True),
        sa.Column("hsn_code", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit", sa.String(10), nullable=False, server_default='NOS'),
        # Values
        sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("cgst_rate", sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column("sgst_rate", sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column("igst_rate", sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column("cess_rate", sa.Numeric(5, 2), nullable=False, server_default='0'),
        # Metadata
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["eway_bill_id"], ["gst_eway_bill.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("eway_bill_id", "line_number", name="uq_eway_bill_item_line"),
    )

    # Create gst_eway_bill_vehicle_update table
    op.create_table(
        "gst_eway_bill_vehicle_update",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("eway_bill_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Update details
        sa.Column("update_type", sa.String(20), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        # Previous values
        sa.Column("previous_vehicle_number", sa.String(20), nullable=True),
        sa.Column("previous_transporter_id", sa.String(15), nullable=True),
        sa.Column("previous_valid_until", sa.DateTime(timezone=True), nullable=True),
        # New values
        sa.Column("new_vehicle_number", sa.String(20), nullable=True),
        sa.Column("new_transporter_id", sa.String(15), nullable=True),
        sa.Column("new_valid_until", sa.DateTime(timezone=True), nullable=True),
        # Location
        sa.Column("from_place", sa.String(100), nullable=True),
        sa.Column("from_state_code", sa.String(2), nullable=True),
        # Reason
        sa.Column("reason", sa.Text(), nullable=True),
        # Response
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        # User tracking
        sa.Column("updated_by_user", postgresql.UUID(as_uuid=True), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["eway_bill_id"], ["gst_eway_bill.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user"], ["mst_user.id"]),
    )
    op.create_index("ix_eway_bill_vehicle_update_time", "gst_eway_bill_vehicle_update", ["eway_bill_id", "update_time"])


def downgrade() -> None:
    op.drop_index("ix_eway_bill_vehicle_update_time", table_name="gst_eway_bill_vehicle_update")
    op.drop_table("gst_eway_bill_vehicle_update")
    op.drop_table("gst_eway_bill_item")
    op.drop_index("ix_eway_bill_validity", table_name="gst_eway_bill")
    op.drop_index("ix_eway_bill_supplier", table_name="gst_eway_bill")
    op.drop_index("ix_eway_bill_number", table_name="gst_eway_bill")
    op.drop_index("ix_eway_bill_org_status", table_name="gst_eway_bill")
    op.drop_table("gst_eway_bill")
    op.drop_index("ix_einvoice_request_irn", table_name="gst_einvoice_request")
    op.drop_index("ix_einvoice_request_invoice", table_name="gst_einvoice_request")
    op.drop_index("ix_einvoice_request_org_status", table_name="gst_einvoice_request")
    op.drop_table("gst_einvoice_request")

    op.execute("DROP TYPE IF EXISTS subsupplytype;")
    op.execute("DROP TYPE IF EXISTS transactiontype;")
    op.execute("DROP TYPE IF EXISTS vehicletype;")
    op.execute("DROP TYPE IF EXISTS transportmode;")
    op.execute("DROP TYPE IF EXISTS ewaybillstatus;")
    op.execute("DROP TYPE IF EXISTS ewaybillprovider;")
    op.execute("DROP TYPE IF EXISTS einvoicerequeststatus;")
    op.execute("DROP TYPE IF EXISTS einvoiceprovider;")
