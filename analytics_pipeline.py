import pandas as pd
import numpy as np
from typing import Dict, List

class EcommercePipeline:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.prepare_data()

    def prepare_data(self):
        """Підготовка даних для аналізу"""
        self.df['order_date'] = pd.to_datetime(self.df['order_date'])
        self.df['month'] = self.df['order_date'].dt.to_period('M')

        # Фільтруємо скасовані замовлення для аналізу, але тримаємо їх для損失 аналізу
        self.df_active = self.df[self.df['order_status'] != 'cancelled'].copy()
        self.df_cancelled = self.df[self.df['order_status'] == 'cancelled'].copy()

    def top_profitable_channels(self, top_n: int = 5) -> pd.DataFrame:
        """Топ прибуткових каналів (тільки виконані замовлення)"""
        result = self.df_active.groupby('sales_channel').agg({
            'gross_revenue_usd': 'sum',
            'cogs_usd': 'sum',
            'shipping_cost_usd': 'sum',
            'ad_spend_usd': 'sum',
            'gross_profit_usd': 'sum',
            'order_id': 'count'
        }).rename(columns={'order_id': 'orders_count'}).sort_values('gross_profit_usd', ascending=False).head(top_n)

        result['margin%'] = (result['gross_profit_usd'] / result['gross_revenue_usd'] * 100).round(2)
        result['roi%'] = (result['gross_profit_usd'] / result['ad_spend_usd'] * 100).round(2)
        result = result[['orders_count', 'gross_revenue_usd', 'cogs_usd', 'ad_spend_usd', 'gross_profit_usd', 'margin%', 'roi%']]
        return result.round(2)

    def losing_campaigns(self, min_spend: float = 0) -> pd.DataFrame:
        """Збиткові кампанії (profit < 0)"""
        campaign_stats = self.df.groupby('campaign').agg({
            'gross_revenue_usd': 'sum',
            'cogs_usd': 'sum',
            'ad_spend_usd': 'sum',
            'gross_profit_usd': 'sum',
            'sales_channel': 'first',
            'category': 'first',
            'order_id': 'count'
        }).rename(columns={'order_id': 'total_orders'})

        # Додаємо кількість скасованих замовлень
        cancelled_by_campaign = self.df_cancelled.groupby('campaign')['order_id'].count()
        campaign_stats['cancelled_orders'] = cancelled_by_campaign
        campaign_stats['cancelled_orders'] = campaign_stats['cancelled_orders'].fillna(0).astype(int)

        result = campaign_stats.query('gross_profit_usd < 0 and ad_spend_usd >= @min_spend').sort_values('gross_profit_usd')

        if not result.empty:
            result['roi%'] = (result['gross_profit_usd'] / result['ad_spend_usd'] * 100).round(1)
            result['cancellation_rate%'] = (result['cancelled_orders'] / result['total_orders'] * 100).round(1)
            result = result[['sales_channel', 'category', 'total_orders', 'cancelled_orders', 'cancellation_rate%',
                           'gross_revenue_usd', 'ad_spend_usd', 'gross_profit_usd', 'roi%']]

        return result.round(2)

    def high_return_categories(self, return_threshold: float = 10) -> pd.DataFrame:
        """Категорії з високим return rate"""
        category_stats = self.df_active.groupby('category').agg({
            'order_id': 'count',
            'is_returned': 'sum',
            'gross_revenue_usd': 'sum',
            'gross_profit_usd': 'sum'
        }).rename(columns={'order_id': 'total_orders', 'is_returned': 'returned_orders'})

        category_stats['return_rate%'] = (category_stats['returned_orders'] / category_stats['total_orders'] * 100).round(2)
        result = category_stats.query('`return_rate%` > @return_threshold').sort_values('return_rate%', ascending=False)

        result = result[['total_orders', 'returned_orders', 'return_rate%', 'gross_revenue_usd', 'gross_profit_usd']]
        return result.round(2)

    def cancellation_analysis(self) -> pd.DataFrame:
        """Аналіз скасованих замовлень по каналам"""
        all_orders = self.df.groupby('sales_channel')['order_id'].count().rename('total_orders')
        cancelled = self.df_cancelled.groupby('sales_channel')['order_id'].count().rename('cancelled_orders')

        result = pd.DataFrame({
            'total_orders': all_orders,
            'cancelled_orders': cancelled.fillna(0).astype(int)
        })
        result['cancellation_rate%'] = (result['cancelled_orders'] / result['total_orders'] * 100).round(2)
        result['lost_ad_spend_usd'] = self.df_cancelled.groupby('sales_channel')['ad_spend_usd'].sum()

        return result.round(2)

    def monthly_trend(self) -> pd.DataFrame:
        """Місячний тренд revenue/profit (без скасованих)"""
        result = self.df_active.groupby('month').agg({
            'gross_revenue_usd': 'sum',
            'cogs_usd': 'sum',
            'ad_spend_usd': 'sum',
            'shipping_cost_usd': 'sum',
            'gross_profit_usd': 'sum',
            'order_id': 'count'
        }).rename(columns={'order_id': 'orders'})

        result['margin%'] = (result['gross_profit_usd'] / result['gross_revenue_usd'] * 100).round(2)
        result = result[['orders', 'gross_revenue_usd', 'cogs_usd', 'ad_spend_usd', 'gross_profit_usd', 'margin%']]
        return result.round(2)

    def product_performance(self, top_n: int = 10) -> pd.DataFrame:
        """Найбільш прибуткові товари"""
        result = self.df_active.groupby(['sku', 'product_name']).agg({
            'quantity': 'sum',
            'gross_revenue_usd': 'sum',
            'gross_profit_usd': 'sum',
            'is_returned': 'sum',
            'order_id': 'count'
        }).rename(columns={'order_id': 'orders', 'is_returned': 'returns'}).sort_values('gross_profit_usd', ascending=False).head(top_n)

        result['return_rate%'] = (result['returns'] / result['orders'] * 100).round(2)
        result = result[['quantity', 'orders', 'returns', 'return_rate%', 'gross_revenue_usd', 'gross_profit_usd']]
        return result.round(2)

    def get_recommendations(self) -> Dict[str, List[str]]:
        """Рекомендації щодо масштабування та скорочення"""
        recommendations = {
            'scale_up': [],
            'cut': [],
            'optimize': []
        }

        # Масштабування
        top_channels = self.top_profitable_channels(3)
        for channel in top_channels.index:
            profit = top_channels.loc[channel, 'gross_profit_usd']
            roi = top_channels.loc[channel, 'roi%']
            recommendations['scale_up'].append(
                f"Канал '{channel}': ROI {roi:.1f}%, прибуток ${profit:,.0f} — збільшуйте бюджет"
            )

        # Скорочення
        losing = self.losing_campaigns()
        if not losing.empty:
            for campaign in losing.index[:3]:
                loss = losing.loc[campaign, 'gross_profit_usd']
                cancel_rate = losing.loc[campaign, 'cancellation_rate%']
                recommendations['cut'].append(
                    f"Кампанія '{campaign}': збиток ${abs(loss):,.0f}, скасування {cancel_rate:.1f}% — припиніть або перебудуйте"
                )

        # Оптимізація
        high_returns = self.high_return_categories()
        if not high_returns.empty:
            for category in high_returns.index[:2]:
                rate = high_returns.loc[category, 'return_rate%']
                revenue = high_returns.loc[category, 'gross_revenue_usd']
                recommendations['optimize'].append(
                    f"Категорія '{category}': return rate {rate:.1f}% (${revenue:,.0f} доходу в ризику) — покращіть опис/якість"
                )

        # Аналіз скасувань
        cancel_analysis = self.cancellation_analysis()
        high_cancel = cancel_analysis[cancel_analysis['cancellation_rate%'] > 15]
        if not high_cancel.empty:
            for channel in high_cancel.index:
                rate = high_cancel.loc[channel, 'cancellation_rate%']
                lost_spend = high_cancel.loc[channel, 'lost_ad_spend_usd']
                recommendations['optimize'].append(
                    f"Канал '{channel}': скасування {rate:.1f}% замовлень (${lost_spend:,.0f} витратили) — перевірте якість трафіку"
                )

        return recommendations

    def generate_report(self) -> str:
        """Повний звіт"""
        report = []
        report.append("=" * 80)
        report.append("📊 АНАЛІТИЧНИЙ ЗВІТ E-COMMERCE")
        report.append("=" * 80)

        # Загальна статистика
        total_revenue = self.df_active['gross_revenue_usd'].sum()
        total_profit = self.df_active['gross_profit_usd'].sum()
        total_orders = len(self.df_active)
        cancelled_count = len(self.df_cancelled)

        report.append(f"\n📈 ЗАГАЛЬНА СТАТИСТИКА")
        report.append(f"  Всього замовлень: {total_orders + cancelled_count} (виконано: {total_orders}, скасовано: {cancelled_count})")
        report.append(f"  Виручка: ${total_revenue:,.2f}")
        report.append(f"  Прибуток: ${total_profit:,.2f}")
        report.append(f"  Маржа: {(total_profit/total_revenue*100):.2f}%")

        report.append("\n" + "=" * 80)
        report.append("🏆 ТОП ПРИБУТКОВІ КАНАЛИ")
        report.append("=" * 80)
        report.append(self.top_profitable_channels().to_string())

        report.append("\n\n⚠️  ЗБИТКОВІ КАМПАНІЇ")
        report.append("=" * 80)
        losing = self.losing_campaigns()
        if losing.empty:
            report.append("✓ Немає збиткових кампаній")
        else:
            report.append(losing.to_string())

        report.append("\n\n🛑 АНАЛІЗ СКАСУВАНЬ")
        report.append("=" * 80)
        report.append(self.cancellation_analysis().to_string())

        report.append("\n\n🔄 КАТЕГОРІЇ З ВИСОКИМ RETURN RATE")
        report.append("=" * 80)
        high_ret = self.high_return_categories()
        if high_ret.empty:
            report.append("✓ Немає проблемних категорій")
        else:
            report.append(high_ret.to_string())

        report.append("\n\n⭐ ТОП ТОВАРИ ПО ПРИБУТКУ")
        report.append("=" * 80)
        report.append(self.product_performance().to_string())

        report.append("\n\n📅 МІСЯЧНИЙ ТРЕНД")
        report.append("=" * 80)
        report.append(self.monthly_trend().to_string())

        report.append("\n\n💡 РЕКОМЕНДАЦІЇ")
        report.append("=" * 80)
        rec = self.get_recommendations()

        if rec['scale_up']:
            report.append("\n✅ МАСШТАБУВАННЯ (збільшуйте бюджет):")
            for r in rec['scale_up']:
                report.append(f"  • {r}")

        if rec['cut']:
            report.append("\n❌ СКОРОЧЕННЯ (припиніть або перебудуйте):")
            for r in rec['cut']:
                report.append(f"  • {r}")

        if rec['optimize']:
            report.append("\n🔧 ОПТИМІЗАЦІЯ:")
            for r in rec['optimize']:
                report.append(f"  • {r}")

        report.append("\n" + "=" * 80)
        return "\n".join(report)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an e-commerce analytics report from a CSV file.")
    parser.add_argument("--csv", required=True, help="Path to the orders CSV file.")
    args = parser.parse_args()
    # Приклад використання
    pipeline = EcommercePipeline(args.csv)
    print(pipeline.generate_report())
