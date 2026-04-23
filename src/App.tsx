import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { AdminLayout } from './layouts/AdminLayout';
import { Toaster } from './components/ui/toaster';
import { useAuth } from './hooks/useAuth';
const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const Login = lazy(() => import('./pages/auth/Login').then((m) => ({ default: m.Login })));
const ForgotPassword = lazy(() => import('./pages/auth/ForgotPassword').then((m) => ({ default: m.ForgotPassword })));
const ResetPassword = lazy(() => import('./pages/auth/ResetPassword').then((m) => ({ default: m.ResetPassword })));
const Profile = lazy(() => import('./pages/Profile').then((m) => ({ default: m.Profile })));
const OrganizationList = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationList })));
const OrganizationForm = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationForm })));
const OrganizationBankAccountList = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationBankAccountList })));
const OrganizationBankAccountForm = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationBankAccountForm })));
const OrganizationAddressList = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationAddressList })));
const OrganizationAddressForm = lazy(() => import('./pages/masters/organizations').then((m) => ({ default: m.OrganizationAddressForm })));
const UnitList = lazy(() => import('./pages/masters/units').then((m) => ({ default: m.UnitList })));
const UnitForm = lazy(() => import('./pages/masters/units').then((m) => ({ default: m.UnitForm })));
const DepartmentList = lazy(() => import('./pages/masters/departments').then((m) => ({ default: m.DepartmentList })));
const DepartmentForm = lazy(() => import('./pages/masters/departments').then((m) => ({ default: m.DepartmentForm })));
const DesignationList = lazy(() => import('./pages/masters/designations').then((m) => ({ default: m.DesignationList })));
const DesignationForm = lazy(() => import('./pages/masters/designations').then((m) => ({ default: m.DesignationForm })));
const UserList = lazy(() => import('./pages/users').then((m) => ({ default: m.UserList })));
const UserForm = lazy(() => import('./pages/users').then((m) => ({ default: m.UserForm })));
const RoleList = lazy(() => import('./pages/roles').then((m) => ({ default: m.RoleList })));
const RoleForm = lazy(() => import('./pages/roles').then((m) => ({ default: m.RoleForm })));
// Finance imports
const FinancialYearList = lazy(() => import('./pages/finance/financial-years').then((m) => ({ default: m.FinancialYearList })));
const FinancialYearForm = lazy(() => import('./pages/finance/financial-years').then((m) => ({ default: m.FinancialYearForm })));
const AccountGroupList = lazy(() => import('./pages/finance/account-groups').then((m) => ({ default: m.AccountGroupList })));
const AccountGroupForm = lazy(() => import('./pages/finance/account-groups').then((m) => ({ default: m.AccountGroupForm })));
const AccountList = lazy(() => import('./pages/finance/accounts').then((m) => ({ default: m.AccountList })));
const AccountForm = lazy(() => import('./pages/finance/accounts').then((m) => ({ default: m.AccountForm })));
const VoucherTypeList = lazy(() => import('./pages/finance/voucher-types').then((m) => ({ default: m.VoucherTypeList })));
const VoucherTypeForm = lazy(() => import('./pages/finance/voucher-types').then((m) => ({ default: m.VoucherTypeForm })));
const VoucherList = lazy(() => import('./pages/finance/vouchers').then((m) => ({ default: m.VoucherList })));
const VoucherForm = lazy(() => import('./pages/finance/vouchers').then((m) => ({ default: m.VoucherForm })));
const VoucherView = lazy(() => import('./pages/finance/vouchers').then((m) => ({ default: m.VoucherView })));
const YearEndClosing = lazy(() => import('./pages/finance/YearEndClosing').then((m) => ({ default: m.YearEndClosing })));
const RecurringVouchers = lazy(() => import('./pages/finance/RecurringVouchers').then((m) => ({ default: m.RecurringVouchers })));
const VoucherTemplates = lazy(() => import('./pages/finance/VoucherTemplates').then((m) => ({ default: m.VoucherTemplates })));
const RecurringVoucherForm = lazy(() => import('./pages/finance/recurring-vouchers').then((m) => ({ default: m.RecurringVoucherForm })));
const GenerateRecurringVoucher = lazy(() => import('./pages/finance/recurring-vouchers').then((m) => ({ default: m.GenerateRecurringVoucher })));
const VoucherTemplateForm = lazy(() => import('./pages/finance/voucher-templates').then((m) => ({ default: m.VoucherTemplateForm })));
const UseVoucherTemplate = lazy(() => import('./pages/finance/voucher-templates').then((m) => ({ default: m.UseVoucherTemplate })));
// GST imports
const GSTRateList = lazy(() => import('./pages/gst/rates').then((m) => ({ default: m.GSTRateList })));
const GstnDashboard = lazy(() => import('./pages/gst/gstn').then((m) => ({ default: m.GstnDashboard })));
const GstnLogin = lazy(() => import('./pages/gst/gstn').then((m) => ({ default: m.GstnLogin })));
const Gstr1Filing = lazy(() => import('./pages/gst/gstn').then((m) => ({ default: m.Gstr1Filing })));
const Gstr3bFiling = lazy(() => import('./pages/gst/gstn').then((m) => ({ default: m.Gstr3bFiling })));
const ItcReconciliation = lazy(() => import('./pages/gst/gstn').then((m) => ({ default: m.ItcReconciliation })));
// TDS imports
const TDSSectionList = lazy(() => import('./pages/tds/sections').then((m) => ({ default: m.TDSSectionList })));
const TDSReturnList = lazy(() => import('./pages/tds').then((m) => ({ default: m.TDSReturnList })));
const TDSChallanList = lazy(() => import('./pages/tds').then((m) => ({ default: m.TDSChallanList })));
const TDSCertificateList = lazy(() => import('./pages/tds').then((m) => ({ default: m.TDSCertificateList })));
// Reports imports
const TrialBalance = lazy(() => import('./pages/reports').then((m) => ({ default: m.TrialBalance })));
const ProfitLoss = lazy(() => import('./pages/reports').then((m) => ({ default: m.ProfitLoss })));
const BalanceSheet = lazy(() => import('./pages/reports').then((m) => ({ default: m.BalanceSheet })));
const AccountLedger = lazy(() => import('./pages/reports').then((m) => ({ default: m.AccountLedger })));
const CashFlowStatement = lazy(() => import('./pages/reports').then((m) => ({ default: m.CashFlowStatement })));
const DayBook = lazy(() => import('./pages/reports').then((m) => ({ default: m.DayBook })));
const ReportDashboard = lazy(() => import('./pages/reports').then((m) => ({ default: m.ReportDashboard })));
const RegulatoryReports = lazy(() => import('./pages/reports').then((m) => ({ default: m.RegulatoryReports })));
const MISReports = lazy(() => import('./pages/reports').then((m) => ({ default: m.MISReports })));
const ReportScheduler = lazy(() => import('./pages/reports').then((m) => ({ default: m.ReportScheduler })));
const ReportHistory = lazy(() => import('./pages/reports').then((m) => ({ default: m.ReportHistory })));
// AP/AR imports
const PaymentTermsList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PaymentTermsList })));
const PaymentTermsForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PaymentTermsForm })));
const VendorList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.VendorList })));
const VendorForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.VendorForm })));
const CustomerList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.CustomerList })));
const CustomerForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.CustomerForm })));
const PurchaseBillList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PurchaseBillList })));
const PurchaseBillForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PurchaseBillForm })));
const PurchaseBillView = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PurchaseBillView })));
const SalesInvoiceList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.SalesInvoiceList })));
const SalesInvoiceForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.SalesInvoiceForm })));
const SalesInvoiceView = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.SalesInvoiceView })));
const PaymentList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PaymentList })));
const PaymentForm = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PaymentForm })));
const PaymentView = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.PaymentView })));
const BankStatementList = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.BankStatementList })));
const BankStatementImport = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.BankStatementImport })));
const BankReconciliation = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.BankReconciliation })));
const BRSReport = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.BRSReport })));
const APAgingReport = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.APAgingReport })));
const ARAgingReport = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.ARAgingReport })));
const APAgingDetail = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.APAgingDetail })));
const ARAgingDetail = lazy(() => import('./pages/ap-ar').then((m) => ({ default: m.ARAgingDetail })));
// Lending imports - Dashboard
import LendingDashboard from './pages/lending/LendingDashboard';

// Lending imports - LOS (Loan Origination)
import EntityList from './pages/lending/los/entities/EntityList';
import EntityForm from './pages/lending/los/entities/EntityForm';
import EntityView from './pages/lending/los/entities/EntityView';
import ProductList from './pages/lending/los/products/ProductList';
import ProductForm from './pages/lending/los/products/ProductForm';
import ProductView from './pages/lending/los/products/ProductView';
import ApplicationList from './pages/lending/los/applications/ApplicationList';
import ApplicationWizard from './pages/lending/los/applications/ApplicationWizard';
import ApplicationView from './pages/lending/los/applications/ApplicationView';
import SanctionList from './pages/lending/los/sanctions/SanctionList';
import SanctionForm from './pages/lending/los/sanctions/SanctionForm';
import SanctionView from './pages/lending/los/sanctions/SanctionView';
import SanctionLetter from './pages/lending/los/sanctions/SanctionLetter';

// Lending imports - LMS (Loan Management)
import LoanAccountList from './pages/lending/lms/accounts/LoanAccountList';
import LoanAccountView from './pages/lending/lms/accounts/LoanAccountView';
import DisbursementList from './pages/lending/lms/disbursements/DisbursementList';
import DisbursementWizard from './pages/lending/lms/disbursements/DisbursementWizard';
import ReceiptList from './pages/lending/lms/receipts/ReceiptList';
import ReceiptForm from './pages/lending/lms/receipts/ReceiptForm';

// Lending imports - Collections
import FollowUpList from './pages/lending/collections/followups/FollowUpList';
import NPAList from './pages/lending/collections/npa/NPAList';
import OTSList from './pages/lending/collections/ots/OTSList';
import OTSWizard from './pages/lending/collections/ots/OTSWizard';
import CollectionLegalCaseList from './pages/lending/collections/legal/LegalCaseList';
import RestructureList from './pages/lending/collections/restructure/RestructureList';
import RestructureCreate from './pages/lending/collections/restructure/RestructureCreate';
import RestructureDetail from './pages/lending/collections/restructure/RestructureDetail';
import RestructureApproval from './pages/lending/collections/restructure/RestructureApproval';

// Lending imports - Treasury
import LenderList from './pages/lending/treasury/lenders/LenderList';
import LenderForm from './pages/lending/treasury/lenders/LenderForm';
import BorrowingList from './pages/lending/treasury/borrowings/BorrowingList';
import BorrowingForm from './pages/lending/treasury/borrowings/BorrowingForm';
import BorrowingView from './pages/lending/treasury/borrowings/BorrowingView';
import TreasuryDashboard from './pages/lending/treasury/TreasuryDashboard';
import ALMDashboard from './pages/lending/treasury/alm/ALMDashboard';
import GapAnalysis from './pages/lending/treasury/alm/GapAnalysis';
import InterestRateRisk from './pages/lending/treasury/alm/InterestRateRisk';

// Regulatory imports
import CRARDashboard from './pages/regulatory/CRARDashboard';

// Lending imports - NACH Integration
import NachBatchList from './pages/lending/nach/NachBatchList';
import NachBatchDetail from './pages/lending/nach/NachBatchDetail';
import CreateNachBatch from './pages/lending/nach/CreateNachBatch';
import NachRetryList from './pages/lending/nach/NachRetryList';

// Lending imports - Account Aggregator Integration
const ConsentList = lazy(() => import('./pages/lending/aa').then((m) => ({ default: m.ConsentList })));
const ConsentDetail = lazy(() => import('./pages/lending/aa').then((m) => ({ default: m.ConsentDetail })));
const RequestConsent = lazy(() => import('./pages/lending/aa').then((m) => ({ default: m.RequestConsent })));
const FetchedData = lazy(() => import('./pages/lending/aa').then((m) => ({ default: m.FetchedData })));
const SessionDetail = lazy(() => import('./pages/lending/aa').then((m) => ({ default: m.SessionDetail })));
// Lending imports - Credit Bureau Integration
const CreditPullList = lazy(() => import('./pages/lending/credit').then((m) => ({ default: m.CreditPullList })));
const CreditPullView = lazy(() => import('./pages/lending/credit').then((m) => ({ default: m.CreditPullView })));
const RequestCreditPull = lazy(() => import('./pages/lending/credit').then((m) => ({ default: m.RequestCreditPull })));
// Lending imports - Reports
import ReportsDashboard from './pages/lending/reports/ReportsDashboard';
import AUMSummary from './pages/lending/reports/portfolio/AUMSummary';
import CollectionEfficiency from './pages/lending/reports/collections/CollectionEfficiency';
import NPAMovement from './pages/lending/reports/npa/NPAMovement';

// Lending imports - Enhanced Features
import NPADashboard from './pages/lending/NPADashboard';
import ScheduleGenerate from './pages/lending/ScheduleGenerate';
import ReceiptCreate from './pages/lending/ReceiptCreate';
import DisbursementCreate from './pages/lending/DisbursementCreate';
import CollateralList from './pages/lending/CollateralList';
import CollateralCreate from './pages/lending/CollateralCreate';
import CollateralValuation from './pages/lending/CollateralValuation';
import EnhancedReceiptList from './pages/lending/ReceiptList';
import ReceiptAllocation from './pages/lending/ReceiptAllocation';
import BulkReceiptUpload from './pages/lending/BulkReceiptUpload';
import EnhancedDisbursementList from './pages/lending/DisbursementList';
import DisbursementApproval from './pages/lending/DisbursementApproval';
import EMICalculator from './pages/lending/EMICalculator';
import ScheduleView from './pages/lending/ScheduleView';

// Fixed Assets imports
const AssetCategoryList = lazy(() => import('./pages/fixed-assets/categories/AssetCategoryList').then((m) => ({ default: m.AssetCategoryList })));
const AssetCategoryForm = lazy(() => import('./pages/fixed-assets/categories/AssetCategoryForm').then((m) => ({ default: m.AssetCategoryForm })));
const AssetList = lazy(() => import('./pages/fixed-assets/assets').then((m) => ({ default: m.AssetList })));
const AssetForm = lazy(() => import('./pages/fixed-assets/assets').then((m) => ({ default: m.AssetForm })));
const AssetView = lazy(() => import('./pages/fixed-assets/assets').then((m) => ({ default: m.AssetView })));
const DepreciationRunPage = lazy(() => import('./pages/fixed-assets/depreciation/DepreciationRun').then((m) => ({ default: m.DepreciationRunPage })));
const RunDepreciation = lazy(() => import('./pages/fixed-assets/depreciation/RunDepreciation').then((m) => ({ default: m.RunDepreciation })));
const DepreciationRunEntries = lazy(() => import('./pages/fixed-assets/depreciation/DepreciationRunEntries').then((m) => ({ default: m.DepreciationRunEntries })));
const PhysicalVerificationList = lazy(() => import('./pages/fixed-assets/verification').then((m) => ({ default: m.PhysicalVerificationList })));
const PhysicalVerificationForm = lazy(() => import('./pages/fixed-assets/verification').then((m) => ({ default: m.PhysicalVerificationForm })));
const MaintenanceList = lazy(() => import('./pages/fixed-assets/maintenance').then((m) => ({ default: m.MaintenanceList })));
const InsuranceList = lazy(() => import('./pages/fixed-assets/insurance').then((m) => ({ default: m.InsuranceList })));
const DisposalList = lazy(() => import('./pages/fixed-assets/disposal').then((m) => ({ default: m.DisposalList })));
// Workflow Management imports
const WorkflowDefinitionList = lazy(() => import('./pages/workflow').then((m) => ({ default: m.WorkflowDefinitionList })));
const WorkflowDefinitionForm = lazy(() => import('./pages/workflow').then((m) => ({ default: m.WorkflowDefinitionForm })));
const WorkflowTaskList = lazy(() => import('./pages/workflow').then((m) => ({ default: m.WorkflowTaskList })));
const WorkflowInstanceList = lazy(() => import('./pages/workflow').then((m) => ({ default: m.WorkflowInstanceList })));
// Settings imports
const IntegrationSettings = lazy(() => import('./pages/settings/IntegrationSettings').then((m) => ({ default: m.IntegrationSettings })));
// HRIS imports
const HRISDashboard = lazy(() => import('./pages/hris').then((m) => ({ default: m.HRISDashboard })));
const EmployeeList = lazy(() => import('./pages/hris/employees').then((m) => ({ default: m.EmployeeList })));
const EmployeeForm = lazy(() => import('./pages/hris/employees').then((m) => ({ default: m.EmployeeForm })));
const EmployeeView = lazy(() => import('./pages/hris/employees').then((m) => ({ default: m.EmployeeView })));
const ShiftList = lazy(() => import('./pages/hris/shifts').then((m) => ({ default: m.ShiftList })));
const ShiftForm = lazy(() => import('./pages/hris/shifts').then((m) => ({ default: m.ShiftForm })));
const HolidayCalendarList = lazy(() => import('./pages/hris/holidays').then((m) => ({ default: m.HolidayCalendarList })));
const HolidayCalendarForm = lazy(() => import('./pages/hris/holidays').then((m) => ({ default: m.HolidayCalendarForm })));
const LeaveTypeList = lazy(() => import('./pages/hris/leave-types').then((m) => ({ default: m.LeaveTypeList })));
const LeaveTypeForm = lazy(() => import('./pages/hris/leave-types').then((m) => ({ default: m.LeaveTypeForm })));
const LeaveApplicationList = lazy(() => import('./pages/hris/leave-applications').then((m) => ({ default: m.LeaveApplicationList })));
const LeaveApplicationForm = lazy(() => import('./pages/hris/leave-applications').then((m) => ({ default: m.LeaveApplicationForm })));
const LeaveApplicationView = lazy(() => import('./pages/hris/leave-applications').then((m) => ({ default: m.LeaveApplicationView })));
const AttendanceList = lazy(() => import('./pages/hris/attendance').then((m) => ({ default: m.AttendanceList })));
const AttendanceRegularization = lazy(() => import('./pages/hris/attendance').then((m) => ({ default: m.AttendanceRegularization })));
const AttendanceProcess = lazy(() => import('./pages/hris/attendance').then((m) => ({ default: m.AttendanceProcess })));
const RegularizationView = lazy(() => import('./pages/hris/attendance').then((m) => ({ default: m.RegularizationView })));
const SeparationList = lazy(() => import('./pages/hris/separation').then((m) => ({ default: m.SeparationList })));
const SeparationInitiate = lazy(() => import('./pages/hris/separation').then((m) => ({ default: m.SeparationInitiate })));
const FnFCalculation = lazy(() => import('./pages/hris/separation').then((m) => ({ default: m.FnFCalculation })));
const TrainingProgramList = lazy(() => import('./pages/hris/training').then((m) => ({ default: m.TrainingProgramList })));
const TrainingProgramForm = lazy(() => import('./pages/hris/training').then((m) => ({ default: m.TrainingProgramForm })));
const TrainingNomination = lazy(() => import('./pages/hris/training').then((m) => ({ default: m.TrainingNomination })));
const TrainingFeedback = lazy(() => import('./pages/hris/training').then((m) => ({ default: m.TrainingFeedback })));
const AppraisalCycleList = lazy(() => import('./pages/hris/performance').then((m) => ({ default: m.AppraisalCycleList })));
const GoalSetting = lazy(() => import('./pages/hris/performance').then((m) => ({ default: m.GoalSetting })));
const SelfAppraisal = lazy(() => import('./pages/hris/performance').then((m) => ({ default: m.SelfAppraisal })));
const ManagerReview = lazy(() => import('./pages/hris/performance').then((m) => ({ default: m.ManagerReview })));
// Payroll imports
const SalaryComponentList = lazy(() => import('./pages/payroll').then((m) => ({ default: m.SalaryComponentList })));
const SalaryComponentForm = lazy(() => import('./pages/payroll').then((m) => ({ default: m.SalaryComponentForm })));
const SalaryStructureList = lazy(() => import('./pages/payroll').then((m) => ({ default: m.SalaryStructureList })));
const SalaryStructureForm = lazy(() => import('./pages/payroll').then((m) => ({ default: m.SalaryStructureForm })));
const EmployeeSalaryList = lazy(() => import('./pages/payroll').then((m) => ({ default: m.EmployeeSalaryList })));
const StatutorySetupList = lazy(() => import('./pages/payroll').then((m) => ({ default: m.StatutorySetupList })));
const StatutorySetupForm = lazy(() => import('./pages/payroll').then((m) => ({ default: m.StatutorySetupForm })));
const PayrollBatchList = lazy(() => import('./pages/payroll').then((m) => ({ default: m.PayrollBatchList })));
const PayrollBatchForm = lazy(() => import('./pages/payroll').then((m) => ({ default: m.PayrollBatchForm })));
const PayrollBatchView = lazy(() => import('./pages/payroll').then((m) => ({ default: m.PayrollBatchView })));
const PayslipView = lazy(() => import('./pages/payroll').then((m) => ({ default: m.PayslipView })));
// Compliance imports
const ComplianceDashboard = lazy(() => import('./pages/compliance').then((m) => ({ default: m.ComplianceDashboard })));
const ComplianceItemList = lazy(() => import('./pages/compliance').then((m) => ({ default: m.ComplianceItemList })));
// Fixed Deposits imports
const FDDashboard = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDDashboard })));
const FDProductList = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDProductList })));
const FDProductForm = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDProductForm })));
const FDInterestSlabs = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDInterestSlabs })));
const FDList = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDList })));
const FDForm = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDForm })));
const FDView = lazy(() => import('./pages/fixed-deposits').then((m) => ({ default: m.FDView })));
// ESS Portal imports
const ESSLogin = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSLogin })));
const ESSLayout = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSLayout })));
const ESSDashboard = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSDashboard })));
const ESSProfile = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSProfile })));
const ESSPayslips = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSPayslips })));
const ESSReimbursements = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSReimbursements })));
const ESSHelpdesk = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSHelpdesk })));
const ESSITDeclaration = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSITDeclaration })));
const ESSExpenseList = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSExpenseList })));
const ESSExpenseForm = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSExpenseForm })));
const ESSExpenseDetail = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSExpenseDetail })));
const ESSTimesheet = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSTimesheet })));
const ESSAssetList = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSAssetList })));
const ESSTrainingList = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSTrainingList })));
const ESSGoals = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSGoals })));
const ESSSelfAppraisal = lazy(() => import('./pages/ess').then((m) => ({ default: m.ESSSelfAppraisal })));
// Customer Portal imports
const PortalLogin = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalLogin })));
const PortalLayout = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalLayout })));
const PortalDashboard = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalDashboard })));
const PortalLoans = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalLoans })));
const PortalLoanDetail = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalLoanDetail })));
const PortalPayments = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalPayments })));
const PortalDocuments = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalDocuments })));
const PortalSupport = lazy(() => import('./pages/portal').then((m) => ({ default: m.PortalSupport })));
// Vendor Portal imports
const VendorLogin = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorLogin })));
const VendorLayout = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorLayout })));
const VendorDashboard = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorDashboard })));
const VendorProfile = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorProfile })));
const VendorPOList = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorPOList })));
const VendorPODetail = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorPODetail })));
const VendorPOAcknowledge = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorPOAcknowledge })));
const VendorPOReject = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorPOReject })));
const VendorInvoiceList = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorInvoiceList })));
const VendorASNList = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorASNList })));
const VendorPaymentList = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorPaymentList })));
const VendorComplianceList = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorComplianceList })));
const VendorComplianceUpload = lazy(() => import('./pages/vendor').then((m) => ({ default: m.VendorComplianceUpload })));
// Legal Module imports
const LegalDashboard = lazy(() => import('./pages/legal').then((m) => ({ default: m.LegalDashboard })));
const LawFirmList = lazy(() => import('./pages/legal').then((m) => ({ default: m.LawFirmList })));
const AdvocateList = lazy(() => import('./pages/legal').then((m) => ({ default: m.AdvocateList })));
const LegalCaseList = lazy(() => import('./pages/legal').then((m) => ({ default: m.LegalCaseList })));
const LegalNoticeList = lazy(() => import('./pages/legal').then((m) => ({ default: m.LegalNoticeList })));
const LegalExpenseList = lazy(() => import('./pages/legal').then((m) => ({ default: m.LegalExpenseList })));
// Notification Module imports
const NotificationList = lazy(() => import('./pages/notification').then((m) => ({ default: m.NotificationList })));
const NotificationDetail = lazy(() => import('./pages/notification').then((m) => ({ default: m.NotificationDetail })));
const NotificationSettings = lazy(() => import('./pages/notification').then((m) => ({ default: m.NotificationSettings })));
const TemplateList = lazy(() => import('./pages/notification').then((m) => ({ default: m.TemplateList })));
const TemplateCreate = lazy(() => import('./pages/notification').then((m) => ({ default: m.TemplateCreate })));
const TemplateEdit = lazy(() => import('./pages/notification').then((m) => ({ default: m.TemplateEdit })));
const NotificationLogPage = lazy(() => import('./pages/notification').then((m) => ({ default: m.NotificationLogPage })));
// DMS Module imports
const DMSDashboard = lazy(() => import('./pages/dms').then((m) => ({ default: m.DMSDashboard })));
const FolderBrowser = lazy(() => import('./pages/dms').then((m) => ({ default: m.FolderBrowser })));
const DocumentUpload = lazy(() => import('./pages/dms').then((m) => ({ default: m.DocumentUpload })));
const DocumentView = lazy(() => import('./pages/dms').then((m) => ({ default: m.DocumentView })));
const DocumentSearch = lazy(() => import('./pages/dms').then((m) => ({ default: m.DocumentSearch })));
const DocumentVersions = lazy(() => import('./pages/dms').then((m) => ({ default: m.DocumentVersions })));
const TagManagement = lazy(() => import('./pages/dms').then((m) => ({ default: m.TagManagement })));
// Accounting Module imports
const GLPostingList = lazy(() => import('./pages/accounting').then((m) => ({ default: m.GLPostingList })));
const GLPostingCreate = lazy(() => import('./pages/accounting').then((m) => ({ default: m.GLPostingCreate })));
const GLPostingDetail = lazy(() => import('./pages/accounting').then((m) => ({ default: m.GLPostingDetail })));
const GLPostingApproval = lazy(() => import('./pages/accounting').then((m) => ({ default: m.GLPostingApproval })));
const PeriodManagement = lazy(() => import('./pages/accounting').then((m) => ({ default: m.PeriodManagement })));
const PeriodClose = lazy(() => import('./pages/accounting').then((m) => ({ default: m.PeriodClose })));
const ApprovalMatrixList = lazy(() => import('./pages/accounting').then((m) => ({ default: m.ApprovalMatrixList })));
const ApprovalMatrixCreate = lazy(() => import('./pages/accounting').then((m) => ({ default: m.ApprovalMatrixCreate })));
const ApprovalMatrixDetail = lazy(() => import('./pages/accounting').then((m) => ({ default: m.ApprovalMatrixDetail })));
const PendingApprovals = lazy(() => import('./pages/accounting').then((m) => ({ default: m.PendingApprovals })));
// KYC Module imports
const CKYCSearch = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CKYCSearch })));
const CKYCDownload = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CKYCDownload })));
const CKYCStatus = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CKYCStatus })));
const CKYCUpload = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CKYCUpload })));
const KYCDocumentList = lazy(() => import('./pages/kyc').then((m) => ({ default: m.KYCDocumentList })));
const KYCDocumentUpload = lazy(() => import('./pages/kyc').then((m) => ({ default: m.KYCDocumentUpload })));
const KYCDocumentVerify = lazy(() => import('./pages/kyc').then((m) => ({ default: m.KYCDocumentVerify })));
const KYCChecklist = lazy(() => import('./pages/kyc').then((m) => ({ default: m.KYCChecklist })));
const CreditBureauPull = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CreditBureauPull })));
const CreditBureauReport = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CreditBureauReport })));
const CreditScoreHistory = lazy(() => import('./pages/kyc').then((m) => ({ default: m.CreditScoreHistory })));
// Inventory Module imports
const InventoryDashboard = lazy(() => import('./pages/inventory').then((m) => ({ default: m.InventoryDashboard })));
const ItemCategoryList = lazy(() => import('./pages/inventory').then((m) => ({ default: m.ItemCategoryList })));
const ItemCategoryForm = lazy(() => import('./pages/inventory').then((m) => ({ default: m.ItemCategoryForm })));
const ItemMasterList = lazy(() => import('./pages/inventory').then((m) => ({ default: m.ItemMasterList })));
const ItemMasterForm = lazy(() => import('./pages/inventory').then((m) => ({ default: m.ItemMasterForm })));
const WarehouseList = lazy(() => import('./pages/inventory').then((m) => ({ default: m.WarehouseList })));
const WarehouseForm = lazy(() => import('./pages/inventory').then((m) => ({ default: m.WarehouseForm })));
const StockIn = lazy(() => import('./pages/inventory').then((m) => ({ default: m.StockIn })));
const StockOut = lazy(() => import('./pages/inventory').then((m) => ({ default: m.StockOut })));
const StockTransfer = lazy(() => import('./pages/inventory').then((m) => ({ default: m.StockTransfer })));
const StockAdjustment = lazy(() => import('./pages/inventory').then((m) => ({ default: m.StockAdjustment })));
const StockReport = lazy(() => import('./pages/inventory').then((m) => ({ default: m.StockReport })));
const InventoryValuation = lazy(() => import('./pages/inventory').then((m) => ({ default: m.InventoryValuation })));
// Treasury Module imports
const RiskDashboard = lazy(() => import('./pages/treasury').then((m) => ({ default: m.RiskDashboard })));
const VaRReport = lazy(() => import('./pages/treasury').then((m) => ({ default: m.VaRReport })));
const LiquidityRisk = lazy(() => import('./pages/treasury').then((m) => ({ default: m.LiquidityRisk })));
const CounterpartyRisk = lazy(() => import('./pages/treasury').then((m) => ({ default: m.CounterpartyRisk })));
const StressTest = lazy(() => import('./pages/treasury').then((m) => ({ default: m.StressTest })));
const InvestmentList = lazy(() => import('./pages/treasury').then((m) => ({ default: m.InvestmentList })));
const InvestmentCreate = lazy(() => import('./pages/treasury').then((m) => ({ default: m.InvestmentCreate })));
const InvestmentMaturity = lazy(() => import('./pages/treasury').then((m) => ({ default: m.InvestmentMaturity })));
// Procurement Module imports
const RFQList = lazy(() => import('./pages/procurement').then((m) => ({ default: m.RFQList })));
const RFQCreate = lazy(() => import('./pages/procurement').then((m) => ({ default: m.RFQCreate })));
const RFQDetail = lazy(() => import('./pages/procurement').then((m) => ({ default: m.RFQDetail })));
const VendorComparison = lazy(() => import('./pages/procurement').then((m) => ({ default: m.VendorComparison })));
const POList = lazy(() => import('./pages/procurement').then((m) => ({ default: m.POList })));
const POCreate = lazy(() => import('./pages/procurement').then((m) => ({ default: m.POCreate })));
const PODetail = lazy(() => import('./pages/procurement').then((m) => ({ default: m.PODetail })));
const POApproval = lazy(() => import('./pages/procurement').then((m) => ({ default: m.POApproval })));
const GRNList = lazy(() => import('./pages/procurement').then((m) => ({ default: m.GRNList })));
const GRNCreate = lazy(() => import('./pages/procurement').then((m) => ({ default: m.GRNCreate })));
// BI/Analytics Module imports
import {
  DashboardList as BIDashboardList,
  DashboardCreate as BIDashboardCreate,
  DashboardEdit as BIDashboardEdit,
  DashboardView as BIDashboardView,
  DashboardAccessConfig,
  WidgetCreate,
  WidgetEdit,
  ChartDefinitionList,
  ChartDefinitionCreate,
  ChartDefinitionEdit,
  DataSourceList,
  DataSourceCreate,
  DataSourceEdit,
} from './pages/bi';

// Auth guard component. Reads from the auth store (no localStorage scraping).
// While bootstrap is running, render nothing to avoid flashing /login.
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { accessToken, isBootstrapping } = useAuth();
  if (isBootstrapping) return null;
  return accessToken ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster />
      <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" role="status" aria-label="Loading" /></div>}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Protected admin routes */}
        <Route
          path="/admin"
          element={
            <PrivateRoute>
              <AdminLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />

          {/* Organizations */}
          <Route path="organizations" element={<OrganizationList />} />
          <Route path="organizations/new" element={<OrganizationForm />} />
          <Route path="organizations/:id/edit" element={<OrganizationForm />} />

          {/* Organization Bank Accounts */}
          <Route path="organizations/:orgId/bank-accounts" element={<OrganizationBankAccountList />} />
          <Route path="organizations/:orgId/bank-accounts/new" element={<OrganizationBankAccountForm />} />
          <Route path="organizations/:orgId/bank-accounts/:id/edit" element={<OrganizationBankAccountForm />} />

          {/* Organization Addresses */}
          <Route path="organizations/:orgId/addresses" element={<OrganizationAddressList />} />
          <Route path="organizations/:orgId/addresses/new" element={<OrganizationAddressForm />} />
          <Route path="organizations/:orgId/addresses/:id/edit" element={<OrganizationAddressForm />} />

          {/* Units */}
          <Route path="units" element={<UnitList />} />
          <Route path="units/new" element={<UnitForm />} />
          <Route path="units/:id/edit" element={<UnitForm />} />

          {/* Departments */}
          <Route path="departments" element={<DepartmentList />} />
          <Route path="departments/new" element={<DepartmentForm />} />
          <Route path="departments/:id/edit" element={<DepartmentForm />} />

          {/* Designations */}
          <Route path="designations" element={<DesignationList />} />
          <Route path="designations/new" element={<DesignationForm />} />
          <Route path="designations/:id/edit" element={<DesignationForm />} />

          {/* Users */}
          <Route path="users" element={<UserList />} />
          <Route path="users/new" element={<UserForm />} />
          <Route path="users/:id/edit" element={<UserForm />} />

          {/* Roles */}
          <Route path="roles" element={<RoleList />} />
          <Route path="roles/new" element={<RoleForm />} />
          <Route path="roles/:id/edit" element={<RoleForm />} />

          {/* Finance - Financial Years */}
          <Route path="finance/financial-years" element={<FinancialYearList />} />
          <Route path="finance/financial-years/new" element={<FinancialYearForm />} />
          <Route path="finance/financial-years/:id/edit" element={<FinancialYearForm />} />

          {/* Finance - Account Groups */}
          <Route path="finance/account-groups" element={<AccountGroupList />} />
          <Route path="finance/account-groups/new" element={<AccountGroupForm />} />
          <Route path="finance/account-groups/:id/edit" element={<AccountGroupForm />} />

          {/* Finance - Accounts */}
          <Route path="finance/accounts" element={<AccountList />} />
          <Route path="finance/accounts/new" element={<AccountForm />} />
          <Route path="finance/accounts/:id/edit" element={<AccountForm />} />

          {/* Finance - Voucher Types */}
          <Route path="finance/voucher-types" element={<VoucherTypeList />} />
          <Route path="finance/voucher-types/new" element={<VoucherTypeForm />} />
          <Route path="finance/voucher-types/:id/edit" element={<VoucherTypeForm />} />

          {/* Finance - Vouchers */}
          <Route path="finance/vouchers" element={<VoucherList />} />
          <Route path="finance/vouchers/new" element={<VoucherForm />} />
          <Route path="finance/vouchers/:id" element={<VoucherView />} />
          <Route path="finance/vouchers/:id/edit" element={<VoucherForm />} />

          {/* Finance - Year-End Closing */}
          <Route path="finance/year-end-closing" element={<YearEndClosing />} />

          {/* Finance - Recurring Vouchers */}
          <Route path="finance/recurring-vouchers" element={<RecurringVouchers />} />
          <Route path="finance/recurring-vouchers/new" element={<RecurringVoucherForm />} />
          <Route path="finance/recurring-vouchers/:id/edit" element={<RecurringVoucherForm />} />
          <Route path="finance/recurring-vouchers/:id/generate" element={<GenerateRecurringVoucher />} />

          {/* Finance - Voucher Templates */}
          <Route path="finance/voucher-templates" element={<VoucherTemplates />} />
          <Route path="finance/voucher-templates/new" element={<VoucherTemplateForm />} />
          <Route path="finance/voucher-templates/:id/edit" element={<VoucherTemplateForm />} />
          <Route path="finance/voucher-templates/:id/use" element={<UseVoucherTemplate />} />

          {/* GST */}
          <Route path="gst/rates" element={<GSTRateList />} />

          {/* GST - GSTN Portal Integration */}
          <Route path="gst/gstn" element={<GstnDashboard />} />
          <Route path="gst/gstn/login" element={<GstnLogin />} />
          <Route path="gst/gstn/gstr1" element={<Gstr1Filing />} />
          <Route path="gst/gstn/gstr3b" element={<Gstr3bFiling />} />
          <Route path="gst/gstn/itc" element={<ItcReconciliation />} />

          {/* TDS */}
          <Route path="tds/sections" element={<TDSSectionList />} />
          <Route path="tds/returns" element={<TDSReturnList />} />
          <Route path="tds/challans" element={<TDSChallanList />} />
          <Route path="tds/certificates" element={<TDSCertificateList />} />

          {/* Financial Reports */}
          <Route path="reports/trial-balance" element={<TrialBalance />} />
          <Route path="reports/profit-loss" element={<ProfitLoss />} />
          <Route path="reports/balance-sheet" element={<BalanceSheet />} />
          <Route path="reports/account-ledger" element={<AccountLedger />} />
          <Route path="reports/cash-flow-statement" element={<CashFlowStatement />} />
          <Route path="reports/day-book" element={<DayBook />} />

          {/* Reports Dashboard & Analytics */}
          <Route path="reports" element={<ReportDashboard />} />
          <Route path="reports/regulatory" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/alm" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/npa" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/crar" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/liquidity" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/large-exposure" element={<RegulatoryReports />} />
          <Route path="reports/regulatory/sector-exposure" element={<RegulatoryReports />} />
          <Route path="reports/mis" element={<MISReports />} />
          <Route path="reports/mis/portfolio" element={<MISReports />} />
          <Route path="reports/mis/disbursement" element={<MISReports />} />
          <Route path="reports/mis/collection" element={<MISReports />} />
          <Route path="reports/mis/delinquency" element={<MISReports />} />
          <Route path="reports/mis/profitability" element={<MISReports />} />
          <Route path="reports/mis/branch-performance" element={<MISReports />} />
          <Route path="reports/scheduler" element={<ReportScheduler />} />
          <Route path="reports/history" element={<ReportHistory />} />

          {/* AP/AR - Payment Terms */}
          <Route path="ap-ar/payment-terms" element={<PaymentTermsList />} />
          <Route path="ap-ar/payment-terms/new" element={<PaymentTermsForm />} />
          <Route path="ap-ar/payment-terms/:id/edit" element={<PaymentTermsForm />} />

          {/* AP/AR - Vendors */}
          <Route path="ap-ar/vendors" element={<VendorList />} />
          <Route path="ap-ar/vendors/new" element={<VendorForm />} />
          <Route path="ap-ar/vendors/:id/edit" element={<VendorForm />} />

          {/* AP/AR - Customers */}
          <Route path="ap-ar/customers" element={<CustomerList />} />
          <Route path="ap-ar/customers/new" element={<CustomerForm />} />
          <Route path="ap-ar/customers/:id/edit" element={<CustomerForm />} />

          {/* AP/AR - Purchase Bills */}
          <Route path="ap-ar/purchase-bills" element={<PurchaseBillList />} />
          <Route path="ap-ar/purchase-bills/new" element={<PurchaseBillForm />} />
          <Route path="ap-ar/purchase-bills/:id" element={<PurchaseBillView />} />
          <Route path="ap-ar/purchase-bills/:id/edit" element={<PurchaseBillForm />} />

          {/* AP/AR - Sales Invoices */}
          <Route path="ap-ar/sales-invoices" element={<SalesInvoiceList />} />
          <Route path="ap-ar/sales-invoices/new" element={<SalesInvoiceForm />} />
          <Route path="ap-ar/sales-invoices/:id" element={<SalesInvoiceView />} />
          <Route path="ap-ar/sales-invoices/:id/edit" element={<SalesInvoiceForm />} />

          {/* AP/AR - Payments & Receipts */}
          <Route path="ap-ar/payments" element={<PaymentList />} />
          <Route path="ap-ar/payments/new" element={<PaymentForm />} />
          <Route path="ap-ar/payments/:id" element={<PaymentView />} />
          <Route path="ap-ar/payments/:id/edit" element={<PaymentForm />} />

          {/* AP/AR - Bank Reconciliation */}
          <Route path="ap-ar/bank-reconciliation" element={<BankStatementList />} />
          <Route path="ap-ar/bank-reconciliation/import" element={<BankStatementImport />} />
          <Route path="ap-ar/bank-reconciliation/reconcile" element={<BankReconciliation />} />
          <Route path="ap-ar/bank-reconciliation/brs-report" element={<BRSReport />} />

          {/* AP/AR - Aging Reports */}
          <Route path="ap-ar/aging-reports/ap" element={<APAgingReport />} />
          <Route path="ap-ar/aging-reports/ar" element={<ARAgingReport />} />
          <Route path="ap-ar/aging-reports/ap-detail/:vendorId" element={<APAgingDetail />} />
          <Route path="ap-ar/aging-reports/ar-detail/:customerId" element={<ARAgingDetail />} />

          {/* Lending - Dashboard */}
          <Route path="lending" element={<LendingDashboard />} />

          {/* Lending - LOS - Entities */}
          <Route path="lending/entities" element={<EntityList />} />
          <Route path="lending/entities/new" element={<EntityForm />} />
          <Route path="lending/entities/:id" element={<EntityView />} />
          <Route path="lending/entities/:id/edit" element={<EntityForm />} />

          {/* Lending - LOS - Products */}
          <Route path="lending/products" element={<ProductList />} />
          <Route path="lending/products/new" element={<ProductForm />} />
          <Route path="lending/products/:id" element={<ProductView />} />
          <Route path="lending/products/:id/edit" element={<ProductForm />} />

          {/* Lending - LOS - Applications */}
          <Route path="lending/applications" element={<ApplicationList />} />
          <Route path="lending/applications/new" element={<ApplicationWizard />} />
          <Route path="lending/applications/:id" element={<ApplicationView />} />
          <Route path="lending/applications/:id/edit" element={<ApplicationWizard />} />

          {/* Lending - LOS - Sanctions */}
          <Route path="lending/sanctions" element={<SanctionList />} />
          <Route path="lending/sanctions/new" element={<SanctionForm />} />
          <Route path="lending/sanctions/:id" element={<SanctionView />} />
          <Route path="lending/sanctions/:id/edit" element={<SanctionForm />} />
          <Route path="lending/sanctions/:id/letter" element={<SanctionLetter />} />

          {/* Lending - LMS - Loan Accounts */}
          <Route path="lending/accounts" element={<LoanAccountList />} />
          <Route path="lending/accounts/:id" element={<LoanAccountView />} />

          {/* Lending - LMS - Disbursements */}
          <Route path="lending/disbursements" element={<DisbursementList />} />
          <Route path="lending/disbursements/new" element={<DisbursementWizard />} />
          <Route path="lending/disbursements/:id" element={<DisbursementWizard />} />

          {/* Lending - LMS - Receipts */}
          <Route path="lending/receipts" element={<ReceiptList />} />
          <Route path="lending/receipts/new" element={<ReceiptForm />} />

          {/* Lending - Collections - Follow-ups */}
          <Route path="lending/collections/followups" element={<FollowUpList />} />

          {/* Lending - Collections - NPA */}
          <Route path="lending/collections/npa" element={<NPAList />} />

          {/* Lending - Collections - OTS */}
          <Route path="lending/collections/ots" element={<OTSList />} />
          <Route path="lending/collections/ots/new" element={<OTSWizard />} />
          <Route path="lending/collections/ots/:id" element={<OTSWizard />} />

          {/* Lending - Collections - Legal */}
          <Route path="lending/collections/legal" element={<CollectionLegalCaseList />} />

          {/* Lending - Collections - Restructure */}
          <Route path="lending/collections/restructure" element={<RestructureList />} />
          <Route path="lending/collections/restructure/new" element={<RestructureCreate />} />
          <Route path="lending/collections/restructure/:id" element={<RestructureDetail />} />
          <Route path="lending/collections/restructure/:id/approve" element={<RestructureApproval />} />

          {/* Legal Module */}
          <Route path="legal" element={<LegalDashboard />} />
          <Route path="legal/law-firms" element={<LawFirmList />} />
          <Route path="legal/advocates" element={<AdvocateList />} />
          <Route path="legal/cases" element={<LegalCaseList />} />
          <Route path="legal/notices" element={<LegalNoticeList />} />
          <Route path="legal/expenses" element={<LegalExpenseList />} />

          {/* Notifications */}
          <Route path="notifications" element={<NotificationList />} />
          <Route path="notifications/:id" element={<NotificationDetail />} />
          <Route path="notifications/settings" element={<NotificationSettings />} />
          <Route path="notifications/templates" element={<TemplateList />} />
          <Route path="notifications/templates/create" element={<TemplateCreate />} />
          <Route path="notifications/templates/:id" element={<TemplateEdit />} />
          <Route path="notifications/templates/:id/edit" element={<TemplateEdit />} />
          <Route path="notifications/logs" element={<NotificationLogPage />} />

          {/* DMS (Document Management System) */}
          <Route path="dms" element={<DMSDashboard />} />
          <Route path="dms/folders" element={<FolderBrowser />} />
          <Route path="dms/upload" element={<DocumentUpload />} />
          <Route path="dms/documents/:id" element={<DocumentView />} />
          <Route path="dms/documents/:id/versions" element={<DocumentVersions />} />
          <Route path="dms/search" element={<DocumentSearch />} />
          <Route path="dms/tags" element={<TagManagement />} />

          {/* Lending - Treasury - Lenders */}
          <Route path="lending/treasury/lenders" element={<LenderList />} />

          {/* Lending - Treasury - Borrowings */}
          <Route path="lending/treasury/borrowings" element={<BorrowingList />} />

          {/* Lending - Treasury - ALM */}
          <Route path="lending/treasury/alm" element={<ALMDashboard />} />
          <Route path="lending/treasury/alm/gap-analysis" element={<GapAnalysis />} />
          <Route path="lending/treasury/alm/interest-rate-risk" element={<InterestRateRisk />} />

          {/* Lending - Reports */}
          <Route path="lending/reports" element={<ReportsDashboard />} />
          <Route path="lending/reports/portfolio/aum" element={<AUMSummary />} />
          <Route path="lending/reports/collections/efficiency" element={<CollectionEfficiency />} />
          <Route path="lending/reports/npa/movement" element={<NPAMovement />} />

          {/* Lending - NACH Integration */}
          <Route path="lending/nach/batches" element={<NachBatchList />} />
          <Route path="lending/nach/batches/new" element={<CreateNachBatch />} />
          <Route path="lending/nach/batches/:batchId" element={<NachBatchDetail />} />
          <Route path="lending/nach/retry" element={<NachRetryList />} />

          {/* Lending - Account Aggregator Integration */}
          <Route path="lending/aa/consents" element={<ConsentList />} />
          <Route path="lending/aa/consents/new" element={<RequestConsent />} />
          <Route path="lending/aa/consents/:consentId" element={<ConsentDetail />} />
          <Route path="lending/aa/sessions/:sessionId" element={<SessionDetail />} />
          <Route path="lending/aa/fetched-data" element={<FetchedData />} />

          {/* Lending - Credit Bureau Integration */}
          <Route path="lending/credit" element={<CreditPullList />} />
          <Route path="lending/credit/request" element={<RequestCreditPull />} />
          <Route path="lending/credit/pulls/:id" element={<CreditPullView />} />

          {/* Lending - Enhanced NPA Management */}
          <Route path="lending/npa" element={<NPADashboard />} />
          <Route path="lending/npa/dashboard" element={<NPADashboard />} />

          {/* Lending - Schedule Management */}
          <Route path="lending/schedules/generate" element={<ScheduleGenerate />} />

          {/* Lending - Enhanced Receipt Management */}
          <Route path="lending/receipts/create" element={<ReceiptCreate />} />

          {/* Lending - Enhanced Disbursement Management */}
          <Route path="lending/disbursements/create" element={<DisbursementCreate />} />

          {/* Lending - Collateral Management */}
          <Route path="lending/collaterals" element={<CollateralList />} />
          <Route path="lending/collaterals/create" element={<CollateralCreate />} />
          <Route path="lending/collaterals/:id/valuation" element={<CollateralValuation />} />

          {/* Lending - Enhanced Receipt Management */}
          <Route path="lending/receipts-enhanced" element={<EnhancedReceiptList />} />
          <Route path="lending/receipts/:id/allocate" element={<ReceiptAllocation />} />
          <Route path="lending/receipts/bulk-upload" element={<BulkReceiptUpload />} />

          {/* Lending - Enhanced Disbursement Management */}
          <Route path="lending/disbursements-enhanced" element={<EnhancedDisbursementList />} />
          <Route path="lending/disbursements/approval" element={<DisbursementApproval />} />

          {/* Lending - Schedule Management */}
          <Route path="lending/schedules/:id" element={<ScheduleView />} />
          <Route path="lending/emi-calculator" element={<EMICalculator />} />

          {/* Accounting - GL Postings */}
          <Route path="accounting/gl-postings" element={<GLPostingList />} />
          <Route path="accounting/gl-postings/new" element={<GLPostingCreate />} />
          <Route path="accounting/gl-postings/:id" element={<GLPostingDetail />} />
          <Route path="accounting/gl-postings/approval" element={<GLPostingApproval />} />
          <Route path="accounting/gl-postings/:id/approval" element={<GLPostingApproval />} />

          {/* Accounting - Period Management */}
          <Route path="accounting/periods" element={<PeriodManagement />} />
          <Route path="accounting/period-close" element={<PeriodClose />} />

          {/* Accounting - Approval Matrix */}
          <Route path="accounting/approval-matrix" element={<ApprovalMatrixList />} />
          <Route path="accounting/approval-matrix/new" element={<ApprovalMatrixCreate />} />
          <Route path="accounting/approval-matrix/:id" element={<ApprovalMatrixDetail />} />
          <Route path="accounting/approval-matrix/:id/edit" element={<ApprovalMatrixCreate />} />
          <Route path="accounting/pending-approvals" element={<PendingApprovals />} />

          {/* KYC - CKYC Integration */}
          <Route path="kyc/ckyc/search" element={<CKYCSearch />} />
          <Route path="kyc/ckyc/download" element={<CKYCDownload />} />
          <Route path="kyc/ckyc/status" element={<CKYCStatus />} />
          <Route path="kyc/ckyc/upload" element={<CKYCUpload />} />

          {/* KYC - Document Management */}
          <Route path="kyc/documents" element={<KYCDocumentList />} />
          <Route path="kyc/documents/upload" element={<KYCDocumentUpload />} />
          <Route path="kyc/documents/:id/verify" element={<KYCDocumentVerify />} />
          <Route path="kyc/checklist" element={<KYCChecklist />} />

          {/* KYC - Credit Bureau */}
          <Route path="kyc/credit-bureau" element={<CreditBureauPull />} />
          <Route path="kyc/credit-bureau/pull" element={<CreditBureauPull />} />
          <Route path="kyc/credit-bureau/report/:reportId" element={<CreditBureauReport />} />
          <Route path="kyc/credit-bureau/history" element={<CreditScoreHistory />} />

          {/* Inventory Module */}
          <Route path="inventory" element={<InventoryDashboard />} />
          <Route path="inventory/dashboard" element={<InventoryDashboard />} />

          {/* Inventory - Item Categories */}
          <Route path="inventory/categories" element={<ItemCategoryList />} />
          <Route path="inventory/categories/new" element={<ItemCategoryForm />} />
          <Route path="inventory/categories/:id/edit" element={<ItemCategoryForm />} />

          {/* Inventory - Items */}
          <Route path="inventory/items" element={<ItemMasterList />} />
          <Route path="inventory/items/new" element={<ItemMasterForm />} />
          <Route path="inventory/items/:id/edit" element={<ItemMasterForm />} />

          {/* Inventory - Warehouses */}
          <Route path="inventory/warehouses" element={<WarehouseList />} />
          <Route path="inventory/warehouses/new" element={<WarehouseForm />} />
          <Route path="inventory/warehouses/:id/edit" element={<WarehouseForm />} />

          {/* Inventory - Stock Transactions */}
          <Route path="inventory/stock-in" element={<StockIn />} />
          <Route path="inventory/stock-out" element={<StockOut />} />
          <Route path="inventory/stock-transfer" element={<StockTransfer />} />
          <Route path="inventory/stock-adjustment" element={<StockAdjustment />} />

          {/* Inventory - Reports */}
          <Route path="inventory/reports" element={<StockReport />} />
          <Route path="inventory/valuation" element={<InventoryValuation />} />

          {/* Treasury - Dashboard */}
          <Route path="treasury" element={<TreasuryDashboard />} />

          {/* Treasury - Lenders */}
          <Route path="treasury/lenders" element={<LenderList />} />
          <Route path="treasury/lenders/new" element={<LenderForm />} />
          <Route path="treasury/lenders/:id" element={<LenderForm />} />
          <Route path="treasury/lenders/:id/edit" element={<LenderForm />} />

          {/* Treasury - Borrowings */}
          <Route path="treasury/borrowings" element={<BorrowingList />} />
          <Route path="treasury/borrowings/new" element={<BorrowingForm />} />
          <Route path="treasury/borrowings/:id" element={<BorrowingView />} />
          <Route path="treasury/borrowings/:id/edit" element={<BorrowingForm />} />

          {/* Treasury - ALM */}
          <Route path="treasury/alm" element={<ALMDashboard />} />
          <Route path="treasury/alm/gap" element={<GapAnalysis />} />
          <Route path="treasury/alm/irs" element={<InterestRateRisk />} />

          {/* Treasury - Risk Management */}
          <Route path="treasury/risk-dashboard" element={<RiskDashboard />} />
          <Route path="treasury/var-report" element={<VaRReport />} />
          <Route path="treasury/liquidity-risk" element={<LiquidityRisk />} />
          <Route path="treasury/counterparty-risk" element={<CounterpartyRisk />} />
          <Route path="treasury/stress-test" element={<StressTest />} />

          {/* Treasury - Investments */}
          <Route path="treasury/investments" element={<InvestmentList />} />
          <Route path="treasury/investments/new" element={<InvestmentCreate />} />
          <Route path="treasury/investments/maturity" element={<InvestmentMaturity />} />
          <Route path="treasury/investments/:id" element={<InvestmentList />} />

          {/* Regulatory */}
          <Route path="regulatory/crar" element={<CRARDashboard />} />
          <Route path="regulatory/exposure" element={<CRARDashboard />} />
          <Route path="regulatory/infrastructure" element={<CRARDashboard />} />
          <Route path="regulatory/returns" element={<CRARDashboard />} />

          {/* Procurement - RFQ */}
          <Route path="procurement/rfq" element={<RFQList />} />
          <Route path="procurement/rfq/new" element={<RFQCreate />} />
          <Route path="procurement/rfq/:id" element={<RFQDetail />} />
          <Route path="procurement/rfq/:id/compare" element={<VendorComparison />} />

          {/* Procurement - Purchase Orders */}
          <Route path="procurement/po" element={<POList />} />
          <Route path="procurement/po/new" element={<POCreate />} />
          <Route path="procurement/po/:id" element={<PODetail />} />
          <Route path="procurement/po/approval" element={<POApproval />} />

          {/* Procurement - GRN */}
          <Route path="procurement/grn" element={<GRNList />} />
          <Route path="procurement/grn/new" element={<GRNCreate />} />
          <Route path="procurement/grn/:id" element={<GRNList />} />

          {/* Fixed Assets - Categories */}
          <Route path="fixed-assets/categories" element={<AssetCategoryList />} />
          <Route path="fixed-assets/categories/new" element={<AssetCategoryForm />} />
          <Route path="fixed-assets/categories/:id/edit" element={<AssetCategoryForm />} />

          {/* Fixed Assets - Assets */}
          <Route path="fixed-assets/assets" element={<AssetList />} />
          <Route path="fixed-assets/assets/new" element={<AssetForm />} />
          <Route path="fixed-assets/assets/:id" element={<AssetView />} />
          <Route path="fixed-assets/assets/:id/edit" element={<AssetForm />} />

          {/* Fixed Assets - Physical Verification */}
          <Route path="fixed-assets/verification" element={<PhysicalVerificationList />} />
          <Route path="fixed-assets/verification/new" element={<PhysicalVerificationForm />} />
          <Route path="fixed-assets/verification/:id" element={<PhysicalVerificationList />} />

          {/* Fixed Assets - Maintenance & AMC */}
          <Route path="fixed-assets/maintenance" element={<MaintenanceList />} />

          {/* Fixed Assets - Insurance */}
          <Route path="fixed-assets/insurance" element={<InsuranceList />} />

          {/* Fixed Assets - Disposal */}
          <Route path="fixed-assets/disposal" element={<DisposalList />} />

          {/* Fixed Assets - Depreciation */}
          <Route path="fixed-assets/depreciation" element={<DepreciationRunPage />} />
          <Route path="fixed-assets/depreciation/run" element={<RunDepreciation />} />
          <Route path="fixed-assets/depreciation/runs/:runId" element={<DepreciationRunEntries />} />

          {/* Workflow Management */}
          <Route path="workflow/definitions" element={<WorkflowDefinitionList />} />
          <Route path="workflow/definitions/new" element={<WorkflowDefinitionForm />} />
          <Route path="workflow/definitions/:id" element={<WorkflowDefinitionList />} />
          <Route path="workflow/definitions/:id/edit" element={<WorkflowDefinitionForm />} />
          <Route path="workflow/tasks" element={<WorkflowTaskList />} />
          <Route path="workflow/instances" element={<WorkflowInstanceList />} />

          {/* Settings */}
          <Route path="settings/integrations" element={<IntegrationSettings />} />

          {/* HRIS - Dashboard */}
          <Route path="hris" element={<HRISDashboard />} />
          <Route path="hris/dashboard" element={<HRISDashboard />} />

          {/* HRIS - Employees */}
          <Route path="hris/employees" element={<EmployeeList />} />
          <Route path="hris/employees/new" element={<EmployeeForm />} />
          <Route path="hris/employees/:id" element={<EmployeeView />} />
          <Route path="hris/employees/:id/edit" element={<EmployeeForm />} />

          {/* HRIS - Shifts */}
          <Route path="hris/shifts" element={<ShiftList />} />
          <Route path="hris/shifts/new" element={<ShiftForm />} />
          <Route path="hris/shifts/:id/edit" element={<ShiftForm />} />

          {/* HRIS - Holiday Calendars */}
          <Route path="hris/holidays" element={<HolidayCalendarList />} />
          <Route path="hris/holidays/new" element={<HolidayCalendarForm />} />
          <Route path="hris/holidays/:id" element={<HolidayCalendarForm />} />
          <Route path="hris/holidays/:id/edit" element={<HolidayCalendarForm />} />

          {/* HRIS - Leave Types */}
          <Route path="hris/leave-types" element={<LeaveTypeList />} />
          <Route path="hris/leave-types/new" element={<LeaveTypeForm />} />
          <Route path="hris/leave-types/:id/edit" element={<LeaveTypeForm />} />

          {/* HRIS - Leave Applications */}
          <Route path="hris/leave-applications" element={<LeaveApplicationList />} />
          <Route path="hris/leave-applications/new" element={<LeaveApplicationForm />} />
          <Route path="hris/leave-applications/:id" element={<LeaveApplicationView />} />
          <Route path="hris/leave-applications/:id/edit" element={<LeaveApplicationForm />} />

          {/* HRIS - Attendance */}
          <Route path="hris/attendance" element={<AttendanceList />} />
          <Route path="hris/attendance/regularization" element={<AttendanceRegularization />} />
          <Route path="hris/attendance/regularization/:id" element={<RegularizationView />} />
          <Route path="hris/attendance/process" element={<AttendanceProcess />} />

          {/* HRIS - Separation & F&F */}
          <Route path="hris/separation" element={<SeparationList />} />
          <Route path="hris/separation/new" element={<SeparationInitiate />} />
          <Route path="hris/separation/:id" element={<SeparationList />} />
          <Route path="hris/separation/:id/fnf" element={<FnFCalculation />} />

          {/* HRIS - Training Management */}
          <Route path="hris/training" element={<TrainingProgramList />} />
          <Route path="hris/training/new" element={<TrainingProgramForm />} />
          <Route path="hris/training/:id" element={<TrainingProgramForm />} />
          <Route path="hris/training/:id/edit" element={<TrainingProgramForm />} />
          <Route path="hris/training/:id/nominations" element={<TrainingNomination />} />
          <Route path="hris/training/:id/feedback" element={<TrainingFeedback />} />

          {/* HRIS - Performance Management */}
          <Route path="hris/performance/cycles" element={<AppraisalCycleList />} />
          <Route path="hris/performance/cycles/new" element={<AppraisalCycleList />} />
          <Route path="hris/performance/cycles/:cycleId" element={<AppraisalCycleList />} />
          <Route path="hris/performance/cycles/:cycleId/goals" element={<GoalSetting />} />
          <Route path="hris/performance/goals" element={<GoalSetting />} />
          <Route path="hris/performance/goals/:employeeId" element={<GoalSetting />} />
          <Route path="hris/performance/self-appraisal" element={<SelfAppraisal />} />
          <Route path="hris/performance/self-appraisal/:cycleId" element={<SelfAppraisal />} />
          <Route path="hris/performance/manager-review" element={<ManagerReview />} />
          <Route path="hris/performance/manager-review/:cycleId/:employeeId" element={<ManagerReview />} />

          {/* Payroll - Salary Components */}
          <Route path="payroll/components" element={<SalaryComponentList />} />
          <Route path="payroll/components/new" element={<SalaryComponentForm />} />
          <Route path="payroll/components/:id/edit" element={<SalaryComponentForm />} />

          {/* Payroll - Salary Structures */}
          <Route path="payroll/structures" element={<SalaryStructureList />} />
          <Route path="payroll/structures/new" element={<SalaryStructureForm />} />
          <Route path="payroll/structures/:id" element={<SalaryStructureForm />} />
          <Route path="payroll/structures/:id/edit" element={<SalaryStructureForm />} />

          {/* Payroll - Employee Salaries */}
          <Route path="payroll/employee-salary" element={<EmployeeSalaryList />} />
          <Route path="payroll/employee-salary/:id" element={<EmployeeSalaryList />} />

          {/* Payroll - Statutory Setup */}
          <Route path="payroll/statutory" element={<StatutorySetupList />} />
          <Route path="payroll/statutory/new" element={<StatutorySetupForm />} />
          <Route path="payroll/statutory/:id/edit" element={<StatutorySetupForm />} />

          {/* Payroll - Batches */}
          <Route path="payroll/batches" element={<PayrollBatchList />} />
          <Route path="payroll/batches/new" element={<PayrollBatchForm />} />
          <Route path="payroll/batches/:id" element={<PayrollBatchView />} />

          {/* Payroll - Payslips */}
          <Route path="payroll/payslips/:id" element={<PayslipView />} />

          {/* Compliance */}
          <Route path="compliance" element={<ComplianceDashboard />} />
          <Route path="compliance/items" element={<ComplianceItemList />} />
          <Route path="compliance/instances" element={<ComplianceDashboard />} />

          {/* Fixed Deposits - Dashboard */}
          <Route path="fixed-deposits/dashboard" element={<FDDashboard />} />

          {/* Fixed Deposits - Products */}
          <Route path="fixed-deposits/products" element={<FDProductList />} />
          <Route path="fixed-deposits/products/new" element={<FDProductForm />} />
          <Route path="fixed-deposits/products/:id/edit" element={<FDProductForm />} />
          <Route path="fixed-deposits/products/:id/slabs" element={<FDInterestSlabs />} />

          {/* Fixed Deposits - Deposits */}
          <Route path="fixed-deposits" element={<FDList />} />
          <Route path="fixed-deposits/new" element={<FDForm />} />
          <Route path="fixed-deposits/:id" element={<FDView />} />

          {/* BI/Analytics - Dashboards */}
          <Route path="bi/dashboards" element={<BIDashboardList />} />
          <Route path="bi/dashboards/new" element={<BIDashboardCreate />} />
          <Route path="bi/dashboards/:id" element={<BIDashboardView />} />
          <Route path="bi/dashboards/:id/edit" element={<BIDashboardEdit />} />
          <Route path="bi/dashboards/:id/access" element={<DashboardAccessConfig />} />

          {/* BI/Analytics - Widgets */}
          <Route path="bi/dashboards/:dashboardId/widgets/new" element={<WidgetCreate />} />
          <Route path="bi/dashboards/:dashboardId/widgets/:widgetId/edit" element={<WidgetEdit />} />

          {/* BI/Analytics - Chart Definitions */}
          <Route path="bi/chart-definitions" element={<ChartDefinitionList />} />
          <Route path="bi/chart-definitions/new" element={<ChartDefinitionCreate />} />
          <Route path="bi/chart-definitions/:id/edit" element={<ChartDefinitionEdit />} />

          {/* BI/Analytics - Data Sources */}
          <Route path="bi/data-sources" element={<DataSourceList />} />
          <Route path="bi/data-sources/new" element={<DataSourceCreate />} />
          <Route path="bi/data-sources/:id/edit" element={<DataSourceEdit />} />
        </Route>

        {/* ESS Portal Routes (separate from admin) */}
        <Route path="/ess/login" element={<ESSLogin />} />
        <Route path="/ess" element={<ESSLayout />}>
          <Route index element={<Navigate to="/ess/dashboard" replace />} />
          <Route path="dashboard" element={<ESSDashboard />} />
          <Route path="profile" element={<ESSProfile />} />
          <Route path="payslips" element={<ESSPayslips />} />
          <Route path="reimbursements" element={<ESSReimbursements />} />
          <Route path="helpdesk" element={<ESSHelpdesk />} />
          <Route path="it-declaration" element={<ESSITDeclaration />} />
          {/* ESS Enhancements */}
          <Route path="expenses" element={<ESSExpenseList />} />
          <Route path="expenses/new" element={<ESSExpenseForm />} />
          <Route path="expenses/:id" element={<ESSExpenseDetail />} />
          <Route path="expenses/:id/edit" element={<ESSExpenseForm />} />
          <Route path="timesheet" element={<ESSTimesheet />} />
          <Route path="assets" element={<ESSAssetList />} />
          <Route path="training" element={<ESSTrainingList />} />
          <Route path="goals" element={<ESSGoals />} />
          <Route path="self-appraisal" element={<ESSSelfAppraisal />} />
        </Route>

        {/* Customer Portal Routes (separate from admin) */}
        <Route path="/portal/login" element={<PortalLogin />} />
        <Route path="/portal" element={<PortalLayout />}>
          <Route index element={<Navigate to="/portal/dashboard" replace />} />
          <Route path="dashboard" element={<PortalDashboard />} />
          <Route path="loans" element={<PortalLoans />} />
          <Route path="loans/:loanId" element={<PortalLoanDetail />} />
          <Route path="payments" element={<PortalPayments />} />
          <Route path="documents" element={<PortalDocuments />} />
          <Route path="support" element={<PortalSupport />} />
        </Route>

        {/* Vendor Portal Routes (separate from admin) */}
        <Route path="/vendor/login" element={<VendorLogin />} />
        <Route path="/vendor" element={<VendorLayout />}>
          <Route index element={<Navigate to="/vendor/dashboard" replace />} />
          <Route path="dashboard" element={<VendorDashboard />} />
          <Route path="profile" element={<VendorProfile />} />
          <Route path="purchase-orders" element={<VendorPOList />} />
          <Route path="purchase-orders/:id" element={<VendorPODetail />} />
          <Route path="purchase-orders/:id/acknowledge" element={<VendorPOAcknowledge />} />
          <Route path="purchase-orders/:id/reject" element={<VendorPOReject />} />
          <Route path="invoices" element={<VendorInvoiceList />} />
          <Route path="asn" element={<VendorASNList />} />
          <Route path="payments" element={<VendorPaymentList />} />
          <Route path="compliance" element={<VendorComplianceList />} />
          <Route path="compliance/upload" element={<VendorComplianceUpload />} />
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/admin" replace />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
