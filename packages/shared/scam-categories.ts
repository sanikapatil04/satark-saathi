export type ScamCategory =
  | 'BANK_KYC'
  | 'OTP_CREDENTIAL_THEFT'
  | 'MONEY_TRANSFER'
  | 'AUTHORITY_IMPERSONATION'
  | 'DIGITAL_ARREST'
  | 'PRIZE_LOTTERY'
  | 'MALICIOUS_LINK'
  | 'GENERIC_SCAM';

export const SCAM_CATEGORIES: Record<ScamCategory, string> = {
  BANK_KYC: 'Bank / KYC Update Scam',
  OTP_CREDENTIAL_THEFT: 'OTP & Credential Theft',
  MONEY_TRANSFER: 'Money Transfer Demand',
  AUTHORITY_IMPERSONATION: 'Authority Impersonation',
  DIGITAL_ARREST: 'Digital Arrest Threat',
  PRIZE_LOTTERY: 'Fake Prize or Lottery',
  MALICIOUS_LINK: 'Suspicious Link Request',
  GENERIC_SCAM: 'General Scam Warning',
};