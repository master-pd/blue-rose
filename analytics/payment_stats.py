#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blue Rose Bot - Payment Statistics Analytics
Track and analyze payment statistics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import Config
from storage.json_engine import JSONEngine

logger = logging.getLogger(__name__)

class PaymentStatsAnalytics:
    """Payment Statistics Analytics"""
    
    def __init__(self):
        self.config = Config
        self.stats_file = self.config.DATA_DIR / "analytics" / "payment_stats.json"
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # Initialize stats file if not exists
        self._initialize_stats()
    
    def _initialize_stats(self):
        """Initialize statistics file"""
        if not self.stats_file.exists():
            default_stats = {
                'metadata': {
                    'description': 'Payment statistics analytics',
                    'version': '1.0.0',
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat()
                },
                'transactions': [],
                'daily_stats': {},
                'monthly_stats': {},
                'plan_stats': {},
                'group_stats': {},
                'revenue_stats': {
                    'total_revenue': 0,
                    'total_transactions': 0,
                    'avg_transaction': 0
                }
            }
            JSONEngine.save_json(self.stats_file, default_stats)
    
    async def log_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Log a payment transaction"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            
            # Add transaction ID if not present
            if 'id' not in transaction:
                transaction['id'] = self._generate_id()
            
            # Add timestamp if not present
            if 'timestamp' not in transaction:
                transaction['timestamp'] = datetime.now().isoformat()
            
            # Add date fields
            trans_date = datetime.fromisoformat(transaction['timestamp'])
            transaction['date'] = trans_date.strftime('%Y-%m-%d')
            transaction['month'] = trans_date.strftime('%Y-%m')
            
            # Add to transactions list
            if 'transactions' not in stats:
                stats['transactions'] = []
            stats['transactions'].append(transaction)
            
            # Update daily stats
            await self._update_daily_stats(stats, transaction)
            
            # Update monthly stats
            await self._update_monthly_stats(stats, transaction)
            
            # Update plan stats
            await self._update_plan_stats(stats, transaction)
            
            # Update group stats
            await self._update_group_stats(stats, transaction)
            
            # Update revenue stats
            await self._update_revenue_stats(stats, transaction)
            
            # Save stats
            stats['metadata']['updated'] = datetime.now().isoformat()
            JSONEngine.save_json(self.stats_file, stats)
            
            logger.info(f"Logged payment transaction: {transaction['id']}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
            return False
    
    async def _update_daily_stats(self, stats: Dict, transaction: Dict):
        """Update daily statistics"""
        date = transaction['date']
        
        if 'daily_stats' not in stats:
            stats['daily_stats'] = {}
        
        if date not in stats['daily_stats']:
            stats['daily_stats'][date] = {
                'transactions': 0,
                'revenue': 0,
                'plans': {},
                'groups': {},
                'methods': {}
            }
        
        daily = stats['daily_stats'][date]
        daily['transactions'] += 1
        
        # Add revenue
        amount = transaction.get('amount', 0)
        if amount:
            daily['revenue'] += amount
        
        # Update plan stats for the day
        plan_type = transaction.get('plan_type', 'unknown')
        if plan_type not in daily['plans']:
            daily['plans'][plan_type] = 0
        daily['plans'][plan_type] += 1
        
        # Update group stats for the day
        group_id = transaction.get('group_id')
        if group_id:
            group_key = str(group_id)
            if group_key not in daily['groups']:
                daily['groups'][group_key] = 0
            daily['groups'][group_key] += 1
        
        # Update payment method stats
        method = transaction.get('method', 'unknown')
        if method not in daily['methods']:
            daily['methods'][method] = 0
        daily['methods'][method] += 1
    
    async def _update_monthly_stats(self, stats: Dict, transaction: Dict):
        """Update monthly statistics"""
        month = transaction['month']
        
        if 'monthly_stats' not in stats:
            stats['monthly_stats'] = {}
        
        if month not in stats['monthly_stats']:
            stats['monthly_stats'][month] = {
                'transactions': 0,
                'revenue': 0,
                'plans': {},
                'groups': {},
                'methods': {},
                'days_active': set()
            }
        
        monthly = stats['monthly_stats'][month]
        monthly['transactions'] += 1
        
        # Add revenue
        amount = transaction.get('amount', 0)
        if amount:
            monthly['revenue'] += amount
        
        # Track active days
        monthly['days_active'].add(transaction['date'])
        
        # Update plan stats for the month
        plan_type = transaction.get('plan_type', 'unknown')
        if plan_type not in monthly['plans']:
            monthly['plans'][plan_type] = 0
        monthly['plans'][plan_type] += 1
        
        # Update group stats for the month
        group_id = transaction.get('group_id')
        if group_id:
            group_key = str(group_id)
            if group_key not in monthly['groups']:
                monthly['groups'][group_key] = 0
            monthly['groups'][group_key] += 1
        
        # Update payment method stats
        method = transaction.get('method', 'unknown')
        if method not in monthly['methods']:
            monthly['methods'][method] = 0
        monthly['methods'][method] += 1
    
    async def _update_plan_stats(self, stats: Dict, transaction: Dict):
        """Update plan statistics"""
        plan_type = transaction.get('plan_type', 'unknown')
        
        if 'plan_stats' not in stats:
            stats['plan_stats'] = {}
        
        if plan_type not in stats['plan_stats']:
            stats['plan_stats'][plan_type] = {
                'transactions': 0,
                'revenue': 0,
                'groups': set(),
                'first_transaction': transaction['timestamp'],
                'last_transaction': transaction['timestamp']
            }
        
        plan = stats['plan_stats'][plan_type]
        plan['transactions'] += 1
        plan['last_transaction'] = transaction['timestamp']
        
        # Add revenue
        amount = transaction.get('amount', 0)
        if amount:
            plan['revenue'] += amount
        
        # Track groups
        group_id = transaction.get('group_id')
        if group_id:
            plan['groups'].add(str(group_id))
    
    async def _update_group_stats(self, stats: Dict, transaction: Dict):
        """Update group statistics"""
        group_id = transaction.get('group_id')
        if not group_id:
            return
        
        group_key = str(group_id)
        
        if 'group_stats' not in stats:
            stats['group_stats'] = {}
        
        if group_key not in stats['group_stats']:
            stats['group_stats'][group_key] = {
                'transactions': 0,
                'revenue': 0,
                'plans': {},
                'first_transaction': transaction['timestamp'],
                'last_transaction': transaction['timestamp']
            }
        
        group = stats['group_stats'][group_key]
        group['transactions'] += 1
        group['last_transaction'] = transaction['timestamp']
        
        # Add revenue
        amount = transaction.get('amount', 0)
        if amount:
            group['revenue'] += amount
        
        # Update plan stats for group
        plan_type = transaction.get('plan_type', 'unknown')
        if plan_type not in group['plans']:
            group['plans'][plan_type] = 0
        group['plans'][plan_type] += 1
    
    async def _update_revenue_stats(self, stats: Dict, transaction: Dict):
        """Update revenue statistics"""
        if 'revenue_stats' not in stats:
            stats['revenue_stats'] = {
                'total_revenue': 0,
                'total_transactions': 0,
                'avg_transaction': 0
            }
        
        revenue_stats = stats['revenue_stats']
        revenue_stats['total_transactions'] += 1
        
        # Add revenue
        amount = transaction.get('amount', 0)
        if amount:
            revenue_stats['total_revenue'] += amount
        
        # Calculate average
        if revenue_stats['total_transactions'] > 0:
            revenue_stats['avg_transaction'] = (
                revenue_stats['total_revenue'] / revenue_stats['total_transactions']
            )
    
    def _generate_id(self) -> str:
        """Generate unique transaction ID"""
        import uuid
        return f"txn_{str(uuid.uuid4())[:8]}"
    
    async def get_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue summary for specified days"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
            
            total_revenue = 0
            total_transactions = 0
            daily_revenue = {}
            
            # Initialize daily revenue
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                daily_revenue[date_str] = 0
                current_date += timedelta(days=1)
            
            # Calculate from transactions
            for transaction in stats.get('transactions', []):
                trans_date = datetime.fromisoformat(transaction['timestamp']).date()
                
                if start_date <= trans_date <= end_date:
                    total_transactions += 1
                    amount = transaction.get('amount', 0)
                    if amount:
                        total_revenue += amount
                    
                    # Add to daily revenue
                    date_str = trans_date.strftime('%Y-%m-%d')
                    if date_str in daily_revenue:
                        daily_revenue[date_str] += amount
            
            # Calculate from daily stats (more efficient for large datasets)
            for date_str, daily in stats.get('daily_stats', {}).items():
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if start_date <= date <= end_date:
                    # Use daily stats if available
                    pass  # Already counted in transaction loop
            
            avg_daily_revenue = total_revenue / days if days > 0 else 0
            avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'revenue': {
                    'total': total_revenue,
                    'average_daily': avg_daily_revenue,
                    'average_transaction': avg_transaction,
                    'daily_breakdown': daily_revenue
                },
                'transactions': {
                    'total': total_transactions,
                    'average_daily': total_transactions / days if days > 0 else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get revenue summary: {e}")
            return {'error': str(e)}
    
    async def get_plan_analytics(self) -> Dict[str, Any]:
        """Get analytics by plan type"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            plan_stats = stats.get('plan_stats', {})
            
            result = {
                'plans': {},
                'summary': {
                    'total_plans': len(plan_stats),
                    'total_revenue': 0,
                    'total_transactions': 0
                }
            }
            
            for plan_type, plan_data in plan_stats.items():
                result['plans'][plan_type] = {
                    'transactions': plan_data.get('transactions', 0),
                    'revenue': plan_data.get('revenue', 0),
                    'unique_groups': len(plan_data.get('groups', set())),
                    'first_transaction': plan_data.get('first_transaction', ''),
                    'last_transaction': plan_data.get('last_transaction', ''),
                    'avg_revenue_per_group': (
                        plan_data.get('revenue', 0) / len(plan_data.get('groups', set()))
                        if len(plan_data.get('groups', set())) > 0 else 0
                    )
                }
                
                # Update summary
                result['summary']['total_revenue'] += plan_data.get('revenue', 0)
                result['summary']['total_transactions'] += plan_data.get('transactions', 0)
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get plan analytics: {e}")
            return {'error': str(e)}
    
    async def get_group_analytics(self, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get analytics for group(s)"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            group_stats = stats.get('group_stats', {})
            
            if group_id:
                group_key = str(group_id)
                if group_key not in group_stats:
                    return {
                        'group_id': group_id,
                        'exists': False,
                        'message': 'No payment history found for this group'
                    }
                
                group_data = group_stats[group_key]
                
                # Get plan distribution
                plan_distribution = []
                total_group_transactions = group_data.get('transactions', 0)
                
                for plan_type, count in group_data.get('plans', {}).items():
                    percentage = (count / total_group_transactions * 100) if total_group_transactions > 0 else 0
                    plan_distribution.append({
                        'plan': plan_type,
                        'transactions': count,
                        'percentage': percentage
                    })
                
                return {
                    'group_id': group_id,
                    'exists': True,
                    'transactions': group_data.get('transactions', 0),
                    'revenue': group_data.get('revenue', 0),
                    'first_transaction': group_data.get('first_transaction', ''),
                    'last_transaction': group_data.get('last_transaction', ''),
                    'plan_distribution': plan_distribution,
                    'avg_transaction_value': (
                        group_data.get('revenue', 0) / group_data.get('transactions', 0)
                        if group_data.get('transactions', 0) > 0 else 0
                    )
                }
            else:
                # Return all groups
                all_groups = []
                for group_key, group_data in group_stats.items():
                    all_groups.append({
                        'group_id': int(group_key),
                        'transactions': group_data.get('transactions', 0),
                        'revenue': group_data.get('revenue', 0),
                        'first_transaction': group_data.get('first_transaction', ''),
                        'last_transaction': group_data.get('last_transaction', '')
                    })
                
                # Sort by revenue (descending)
                all_groups.sort(key=lambda x: x['revenue'], reverse=True)
                
                return {
                    'total_groups': len(all_groups),
                    'total_revenue': sum(g['revenue'] for g in all_groups),
                    'total_transactions': sum(g['transactions'] for g in all_groups),
                    'top_groups': all_groups[:10],  # Top 10 by revenue
                    'average_revenue_per_group': (
                        sum(g['revenue'] for g in all_groups) / len(all_groups)
                        if len(all_groups) > 0 else 0
                    )
                }
        
        except Exception as e:
            logger.error(f"Failed to get group analytics: {e}")
            return {'error': str(e)}
    
    async def get_payment_method_analytics(self) -> Dict[str, Any]:
        """Get analytics by payment method"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            
            method_stats = {}
            
            # Aggregate from transactions
            for transaction in stats.get('transactions', []):
                method = transaction.get('method', 'unknown')
                amount = transaction.get('amount', 0)
                
                if method not in method_stats:
                    method_stats[method] = {
                        'transactions': 0,
                        'revenue': 0
                    }
                
                method_stats[method]['transactions'] += 1
                method_stats[method]['revenue'] += amount
            
            # Also check monthly stats for method distribution
            for month_data in stats.get('monthly_stats', {}).values():
                for method, count in month_data.get('methods', {}).items():
                    if method not in method_stats:
                        method_stats[method] = {
                            'transactions': 0,
                            'revenue': 0
                        }
                    # Note: monthly stats don't have revenue by method, so we can't add revenue here
            
            # Calculate percentages
            total_transactions = sum(m['transactions'] for m in method_stats.values())
            total_revenue = sum(m['revenue'] for m in method_stats.values())
            
            result = {}
            for method, data in method_stats.items():
                transaction_pct = (data['transactions'] / total_transactions * 100) if total_transactions > 0 else 0
                revenue_pct = (data['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
                
                result[method] = {
                    'transactions': data['transactions'],
                    'revenue': data['revenue'],
                    'transaction_percentage': transaction_pct,
                    'revenue_percentage': revenue_pct,
                    'avg_transaction_value': (
                        data['revenue'] / data['transactions']
                        if data['transactions'] > 0 else 0
                    )
                }
            
            return {
                'methods': result,
                'summary': {
                    'total_transactions': total_transactions,
                    'total_revenue': total_revenue,
                    'unique_methods': len(method_stats)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get payment method analytics: {e}")
            return {'error': str(e)}
    
    async def get_conversion_metrics(self) -> Dict[str, Any]:
        """Get conversion metrics and trends"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            
            # Calculate conversion rate (transactions per active group)
            active_groups = set()
            for group_key in stats.get('group_stats', {}).keys():
                active_groups.add(group_key)
            
            total_transactions = stats.get('revenue_stats', {}).get('total_transactions', 0)
            total_groups = len(active_groups)
            
            # Calculate monthly trends
            monthly_trends = []
            for month, month_data in sorted(stats.get('monthly_stats', {}).items()):
                monthly_trends.append({
                    'month': month,
                    'transactions': month_data.get('transactions', 0),
                    'revenue': month_data.get('revenue', 0),
                    'active_groups': len(month_data.get('groups', {})),
                    'active_days': len(month_data.get('days_active', set()))
                })
            
            # Calculate plan conversion rates
            plan_conversion = {}
            plan_stats = stats.get('plan_stats', {})
            
            for plan_type, plan_data in plan_stats.items():
                unique_groups = len(plan_data.get('groups', set()))
                transactions = plan_data.get('transactions', 0)
                
                plan_conversion[plan_type] = {
                    'unique_groups': unique_groups,
                    'total_transactions': transactions,
                    'transactions_per_group': (
                        transactions / unique_groups if unique_groups > 0 else 0
                    ),
                    'revenue_per_group': (
                        plan_data.get('revenue', 0) / unique_groups if unique_groups > 0 else 0
                    )
                }
            
            return {
                'conversion_rates': {
                    'total_groups': total_groups,
                    'total_transactions': total_transactions,
                    'transactions_per_group': (
                        total_transactions / total_groups if total_groups > 0 else 0
                    ),
                    'active_group_percentage': 100,  # All groups with payments are active
                },
                'monthly_trends': monthly_trends[-12:],  # Last 12 months
                'plan_conversion': plan_conversion,
                'revenue_trends': {
                    'total_revenue': stats.get('revenue_stats', {}).get('total_revenue', 0),
                    'avg_monthly_growth': self._calculate_avg_growth(monthly_trends)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get conversion metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_avg_growth(self, monthly_trends: List[Dict]) -> float:
        """Calculate average monthly growth rate"""
        if len(monthly_trends) < 2:
            return 0
        
        revenues = [m['revenue'] for m in monthly_trends]
        growth_rates = []
        
        for i in range(1, len(revenues)):
            if revenues[i-1] > 0:
                growth_rate = ((revenues[i] - revenues[i-1]) / revenues[i-1]) * 100
                growth_rates.append(growth_rate)
        
        return sum(growth_rates) / len(growth_rates) if growth_rates else 0
    
    async def generate_report(self, report_type: str = 'summary') -> str:
        """Generate payment analytics report"""
        try:
            if report_type == 'summary':
                revenue = await self.get_revenue_summary(days=30)
                plan_analytics = await self.get_plan_analytics()
                method_analytics = await self.get_payment_method_analytics()
                
                report_lines = [
                    "💰 **Payment Analytics Report**",
                    f"**Period:** Last 30 days",
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "📊 **Revenue Summary**",
                    f"• Total Revenue: ৳{revenue.get('revenue', {}).get('total', 0):.2f}",
                    f"• Total Transactions: {revenue.get('transactions', {}).get('total', 0)}",
                    f"• Avg Daily Revenue: ৳{revenue.get('revenue', {}).get('average_daily', 0):.2f}",
                    "",
                    "📈 **Plan Performance**"
                ]
                
                for plan_type, plan_data in plan_analytics.get('plans', {}).items():
                    report_lines.append(
                        f"• {plan_type.title()}: "
                        f"{plan_data.get('transactions', 0)} transactions, "
                        f"৳{plan_data.get('revenue', 0):.2f} revenue"
                    )
                
                report_lines.extend([
                    "",
                    "💳 **Payment Methods**"
                ])
                
                for method, method_data in method_analytics.get('methods', {}).items():
                    report_lines.append(
                        f"• {method.title()}: "
                        f"{method_data.get('transactions', 0)} transactions "
                        f"({method_data.get('transaction_percentage', 0):.1f}%)"
                    )
                
                return "\n".join(report_lines)
            
            elif report_type == 'detailed':
                # More detailed report
                pass
            
            return "Report type not supported"
        
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return f"Error generating report: {e}"
    
    async def cleanup_old_data(self, months_to_keep: int = 12) -> int:
        """Cleanup old payment statistics"""
        try:
            stats = JSONEngine.load_json(self.stats_file, {})
            
            cutoff_date = (datetime.now() - timedelta(days=months_to_keep*30)).date()
            cutoff_timestamp = datetime.combine(cutoff_date, datetime.min.time()).isoformat()
            
            # Filter transactions
            if 'transactions' in stats:
                original_count = len(stats['transactions'])
                stats['transactions'] = [
                    txn for txn in stats['transactions']
                    if datetime.fromisoformat(txn['timestamp']).date() >= cutoff_date
                ]
                removed_count = original_count - len(stats['transactions'])
                
                # Recalculate all stats from remaining transactions
                await self._recalculate_all_stats(stats)
                
                # Save cleaned stats
                stats['metadata']['updated'] = datetime.now().isoformat()
                JSONEngine.save_json(self.stats_file, stats)
                
                logger.info(f"Cleaned up {removed_count} old transaction records")
                return removed_count
            
            return 0
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    async def _recalculate_all_stats(self, stats: Dict):
        """Recalculate all statistics from transactions"""
        # Clear all stats
        stats['daily_stats'] = {}
        stats['monthly_stats'] = {}
        stats['plan_stats'] = {}
        stats['group_stats'] = {}
        stats['revenue_stats'] = {
            'total_revenue': 0,
            'total_transactions': 0,
            'avg_transaction': 0
        }
        
        # Recalculate from remaining transactions
        for transaction in stats.get('transactions', []):
            await self._update_daily_stats(stats, transaction)
            await self._update_monthly_stats(stats, transaction)
            await self._update_plan_stats(stats, transaction)
            await self._update_group_stats(stats, transaction)
            await self._update_revenue_stats(stats, transaction)