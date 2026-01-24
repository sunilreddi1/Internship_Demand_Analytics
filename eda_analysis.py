"""
Exploratory Data Analysis for Internship Demand Analytics
========================================================

This script performs comprehensive exploratory data analysis on the internship dataset
to understand patterns, trends, and insights for the internship demand prediction system.

Author: V. Sunil Reddy
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Try to import optional libraries
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("⚠️  seaborn not available - using matplotlib only")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("⚠️  plotly not available - interactive plots disabled")

# Set style for matplotlib
plt.style.use('default')
if HAS_SEABORN:
    sns.set_palette("husl")

class InternshipEDA:
    """
    Comprehensive EDA class for internship dataset analysis
    """

    def __init__(self, data_path='adzuna_internships_raw.csv'):
        """Initialize EDA with dataset path"""
        self.data_path = data_path
        self.df = None
        self.load_data()

    def load_data(self):
        """Load and perform initial data cleaning"""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"✅ Data loaded successfully! Shape: {self.df.shape}")
            print(f"📊 Total internships: {len(self.df)}")
            print(f"🏢 Unique companies: {self.df['company'].nunique()}")
            print(f"📍 Unique locations: {self.df['location'].nunique()}")
            print(f"🏷️  Unique categories: {self.df['category'].nunique()}")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None

    def data_overview(self):
        """Provide comprehensive data overview"""
        print("\n" + "="*60)
        print("📊 DATA OVERVIEW")
        print("="*60)

        print(f"\n🔍 Dataset Shape: {self.df.shape}")
        print(f"📈 Memory Usage: {self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

        print(f"\n📋 Column Information:")
        print("-" * 50)
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            non_null = self.df[col].count()
            null_count = self.df[col].isnull().sum()
            unique_count = self.df[col].nunique()
            print(f"{col:<20} | {dtype:<10} | {non_null:<6} | {null_count:<6} | {unique_count:<8}")

    def missing_values_analysis(self):
        """Analyze missing values in the dataset"""
        print("\n" + "="*60)
        print("🔍 MISSING VALUES ANALYSIS")
        print("="*60)

        missing_data = self.df.isnull().sum()
        missing_percent = (missing_data / len(self.df)) * 100

        missing_df = pd.DataFrame({
            'Missing Count': missing_data,
            'Missing Percentage': missing_percent
        }).sort_values('Missing Count', ascending=False)

        missing_df = missing_df[missing_df['Missing Count'] > 0]

        if not missing_df.empty:
            print("\nColumns with missing values:")
            print("-" * 60)
            for idx, row in missing_df.iterrows():
                print(f"{idx:<20} | {int(row['Missing Count']):<6} | {row['Missing Percentage']:.2f}%")
        else:
            print("✅ No missing values found!")

    def numerical_analysis(self):
        """Analyze numerical columns"""
        print("\n" + "="*60)
        print("🔢 NUMERICAL COLUMNS ANALYSIS")
        print("="*60)

        numerical_cols = ['salary_min', 'salary_max', 'stipend', 'demand_score', 'applications_count']

        for col in numerical_cols:
            if col in self.df.columns:
                print(f"\n📊 {col.upper()}:")
                print("-" * 30)
                print(self.df[col].describe())

                # Check for zeros or negative values
                zero_count = (self.df[col] == 0).sum()
                negative_count = (self.df[col] < 0).sum()

                if zero_count > 0:
                    print(f"Zero values: {zero_count} ({zero_count/len(self.df)*100:.2f}%)")
                if negative_count > 0:
                    print(f"Negative values: {negative_count} ({negative_count/len(self.df)*100:.2f}%)")

    def categorical_analysis(self):
        """Analyze categorical columns"""
        print("\n" + "="*60)
        print("🏷️  CATEGORICAL COLUMNS ANALYSIS")
        print("="*60)

        categorical_cols = ['location', 'category', 'contract_type', 'is_remote']

        for col in categorical_cols:
            if col in self.df.columns:
                print(f"\n📊 {col.upper()}:")
                print("-" * 30)
                value_counts = self.df[col].value_counts()
                print(f"Unique values: {len(value_counts)}")

                # Show top 10 values
                print("\nTop 10 values:")
                for i, (val, count) in enumerate(value_counts.head(10).items()):
                    percentage = (count / len(self.df)) * 100
                    print(f"{i+1:2d}. {val:<25} | {count:<6} | {percentage:.2f}%")

    def location_analysis(self):
        """Detailed analysis of internship locations"""
        print("\n" + "="*60)
        print("📍 LOCATION ANALYSIS")
        print("="*60)

        location_stats = self.df.groupby('location').agg({
            'title': 'count',
            'stipend': ['mean', 'median', 'min', 'max'],
            'demand_score': ['mean', 'median'],
            'applications_count': ['mean', 'median']
        }).round(2)

        location_stats.columns = ['count', 'stipend_mean', 'stipend_median', 'stipend_min', 'stipend_max',
                                 'demand_mean', 'demand_median', 'apps_mean', 'apps_median']

        location_stats = location_stats.sort_values('count', ascending=False)

        print("\n🏙️  Top 15 Locations by Internship Count:")
        print("-" * 80)
        for i, (location, row) in enumerate(location_stats.head(15).iterrows()):
            print(f"{i+1:2d}. {location:<20} | Count: {int(row['count']):<4} | "
                  f"Avg Stipend: ₹{row['stipend_mean']:>8.0f} | "
                  f"Avg Demand: {row['demand_mean']:>6.2f}")

    def category_analysis(self):
        """Detailed analysis of internship categories"""
        print("\n" + "="*60)
        print("🏷️  CATEGORY ANALYSIS")
        print("="*60)

        category_stats = self.df.groupby('category').agg({
            'title': 'count',
            'stipend': ['mean', 'median'],
            'demand_score': ['mean', 'median'],
            'applications_count': ['mean', 'median']
        }).round(2)

        category_stats.columns = ['count', 'stipend_mean', 'stipend_median',
                                 'demand_mean', 'demand_median', 'apps_mean', 'apps_median']

        category_stats = category_stats.sort_values('count', ascending=False)

        print("\n📂 Top Categories by Internship Count:")
        print("-" * 80)
        for i, (category, row) in enumerate(category_stats.head(10).iterrows()):
            print(f"{i+1:2d}. {category:<30} | Count: {int(row['count']):<4} | "
                  f"Avg Stipend: ₹{row['stipend_mean']:>8.0f} | "
                  f"Avg Demand: {row['demand_mean']:>6.2f}")

    def skills_analysis(self):
        """Analyze skills required across internships"""
        print("\n" + "="*60)
        print("🛠️  SKILLS ANALYSIS")
        print("="*60)

        # Split skills and count frequency
        all_skills = []
        for skills_str in self.df['skills_required'].dropna():
            if isinstance(skills_str, str):
                skills = [skill.strip() for skill in skills_str.split(',')]
                all_skills.extend(skills)

        skill_counts = pd.Series(all_skills).value_counts()

        print(f"\n📊 Total unique skills mentioned: {len(skill_counts)}")
        print("\n🔝 Top 20 Most In-Demand Skills:")
        print("-" * 50)
        for i, (skill, count) in enumerate(skill_counts.head(20).items()):
            percentage = (count / len(self.df)) * 100
            print(f"{i+1:2d}. {skill:<20} | {count:<6} | {percentage:.2f}%")

    def stipend_analysis(self):
        """Analyze stipend distributions and patterns"""
        print("\n" + "="*60)
        print("💰 STIPEND ANALYSIS")
        print("="*60)

        # Filter out zero stipends for meaningful analysis
        stipend_data = self.df[self.df['stipend'] > 0]['stipend']

        print(f"\n📊 Stipend Statistics (excluding ₹0):")
        print("-" * 40)
        print(stipend_data.describe())

        print(f"\n💵 Stipend Ranges:")
        print("-" * 30)
        ranges = [0, 5000, 10000, 15000, 20000, 30000, 50000, float('inf')]
        range_labels = ['₹0-5K', '₹5K-10K', '₹10K-15K', '₹15K-20K', '₹20K-30K', '₹30K-50K', '₹50K+']

        for i in range(len(ranges)-1):
            count = ((self.df['stipend'] >= ranges[i]) & (self.df['stipend'] < ranges[i+1])).sum()
            percentage = (count / len(self.df)) * 100
            print(f"{range_labels[i]:<12} | {count:<6} | {percentage:.2f}%")

    def demand_analysis(self):
        """Analyze demand scores and patterns"""
        print("\n" + "="*60)
        print("📈 DEMAND SCORE ANALYSIS")
        print("="*60)

        print(f"\n📊 Demand Score Statistics:")
        print("-" * 35)
        print(self.df['demand_score'].describe())

        print(f"\n🎯 Demand Score Ranges:")
        print("-" * 30)
        demand_ranges = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        range_labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']

        for i in range(len(demand_ranges)-1):
            count = ((self.df['demand_score'] >= demand_ranges[i]) &
                    (self.df['demand_score'] < demand_ranges[i+1])).sum()
            percentage = (count / len(self.df)) * 100
            print(f"{range_labels[i]:<8} | {count:<6} | {percentage:.2f}%")

    def correlation_analysis(self):
        """Analyze correlations between numerical variables"""
        print("\n" + "="*60)
        print("🔗 CORRELATION ANALYSIS")
        print("="*60)

        numerical_cols = ['salary_min', 'salary_max', 'stipend', 'demand_score', 'applications_count']
        available_cols = [col for col in numerical_cols if col in self.df.columns]

        if len(available_cols) > 1:
            corr_matrix = self.df[available_cols].corr()

            print("\n📊 Correlation Matrix:")
            print("-" * 40)
            print(corr_matrix.round(3))

            print("\n🔍 Key Correlations:")
            print("-" * 30)

            # Find strong correlations
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.3:  # Only show correlations > 0.3
                        col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                        strength = "Strong" if abs(corr_value) > 0.7 else "Moderate"
                        direction = "Positive" if corr_value > 0 else "Negative"
                        print(f"{col1} ↔ {col2}: {corr_value:.3f} ({strength} {direction})")

    def create_visualizations(self):
        """Create comprehensive visualizations"""
        print("\n" + "="*60)
        print("📊 CREATING VISUALIZATIONS")
        print("="*60)

        # Set up the plotting area
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Internship Dataset - Key Insights', fontsize=16, fontweight='bold')

        # 1. Top 10 Locations
        location_counts = self.df['location'].value_counts().head(10)
        axes[0, 0].bar(range(len(location_counts)), location_counts.values)
        axes[0, 0].set_xticks(range(len(location_counts)))
        axes[0, 0].set_xticklabels(location_counts.index, rotation=45, ha='right')
        axes[0, 0].set_title('Top 10 Internship Locations')
        axes[0, 0].set_ylabel('Number of Internships')

        # 2. Stipend Distribution
        stipend_data = self.df[self.df['stipend'] > 0]['stipend']
        axes[0, 1].hist(stipend_data, bins=30, edgecolor='black', alpha=0.7)
        axes[0, 1].set_title('Stipend Distribution')
        axes[0, 1].set_xlabel('Stipend (₹)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].axvline(stipend_data.mean(), color='red', linestyle='--', label=f'Mean: ₹{stipend_data.mean():.0f}')
        axes[0, 1].legend()

        # 3. Demand Score Distribution
        axes[1, 0].hist(self.df['demand_score'], bins=20, edgecolor='black', alpha=0.7, color='green')
        axes[1, 0].set_title('Demand Score Distribution')
        axes[1, 0].set_xlabel('Demand Score')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].axvline(self.df['demand_score'].mean(), color='red', linestyle='--',
                          label=f'Mean: {self.df["demand_score"].mean():.2f}')
        axes[1, 0].legend()

        # 4. Top 10 Categories
        category_counts = self.df['category'].value_counts().head(10)
        axes[1, 1].bar(range(len(category_counts)), category_counts.values)
        axes[1, 1].set_xticks(range(len(category_counts)))
        axes[1, 1].set_xticklabels([cat.split()[0] for cat in category_counts.index], rotation=45, ha='right')
        axes[1, 1].set_title('Top 10 Internship Categories')
        axes[1, 1].set_ylabel('Number of Internships')

        plt.tight_layout()
        plt.savefig('eda_visualizations.png', dpi=300, bbox_inches='tight')
        print("✅ Visualizations saved as 'eda_visualizations.png'")

        # Create interactive Plotly visualizations
        self.create_interactive_plots()

    def create_interactive_plots(self):
        """Create interactive visualizations using Plotly"""
        if not HAS_PLOTLY:
            print("⚠️  Skipping interactive plots - plotly not available")
            return

        # Skills frequency chart
        all_skills = []
        for skills_str in self.df['skills_required'].dropna():
            if isinstance(skills_str, str):
                skills = [skill.strip() for skill in skills_str.split(',')]
                all_skills.extend(skills)

        skill_counts = pd.Series(all_skills).value_counts().head(20)

        fig_skills = px.bar(skill_counts,
                           title='Top 20 Most In-Demand Skills',
                           labels={'index': 'Skill', 'value': 'Frequency'},
                           color=skill_counts.values,
                           color_continuous_scale='Viridis')
        fig_skills.write_html('skills_analysis.html')
        print("✅ Interactive skills analysis saved as 'skills_analysis.html'")

        # Location vs Average Stipend
        location_stipend = self.df.groupby('location')['stipend'].mean().sort_values(ascending=False).head(15)

        fig_location = px.bar(location_stipend,
                             title='Average Stipend by Location (Top 15)',
                             labels={'value': 'Average Stipend (₹)', 'index': 'Location'},
                             color=location_stipend.values,
                             color_continuous_scale='Blues')
        fig_location.write_html('location_stipend_analysis.html')
        print("✅ Interactive location analysis saved as 'location_stipend_analysis.html'")

    def generate_report(self):
        """Generate comprehensive EDA report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE EDA REPORT SUMMARY")
        print("="*80)

        print("\n🔍 DATASET OVERVIEW:")
        print(f"   • Total internships: {len(self.df):,}")
        print(f"   • Unique companies: {self.df['company'].nunique():,}")
        print(f"   • Unique locations: {self.df['location'].nunique()}")
        print(f"   • Unique categories: {self.df['category'].nunique()}")

        # Key insights
        print("\n💡 KEY INSIGHTS:")
        print(f"   • Average stipend: ₹{self.df[self.df['stipend'] > 0]['stipend'].mean():.0f}")
        print(f"   • Average demand score: {self.df['demand_score'].mean():.2f}")
        print(f"   • Most common location: {self.df['location'].value_counts().index[0]}")
        print(f"   • Most common category: {self.df['category'].value_counts().index[0]}")

        # Skills insights
        all_skills = []
        for skills_str in self.df['skills_required'].dropna():
            if isinstance(skills_str, str):
                skills = [skill.strip() for skill in skills_str.split(',')]
                all_skills.extend(skills)
        skill_counts = pd.Series(all_skills).value_counts()
        print(f"   • Most in-demand skill: {skill_counts.index[0]}")

        print("\n📊 ANALYSIS COMPLETED!")
        print("   Files generated:")
        print("   • eda_visualizations.png - Static plots")
        print("   • skills_analysis.html - Interactive skills chart")
        print("   • location_stipend_analysis.html - Interactive location analysis")

    def run_full_analysis(self):
        """Run complete EDA analysis"""
        print("🚀 STARTING COMPREHENSIVE EDA ANALYSIS")
        print("="*60)

        # Run all analysis methods
        self.data_overview()
        self.missing_values_analysis()
        self.numerical_analysis()
        self.categorical_analysis()
        self.location_analysis()
        self.category_analysis()
        self.skills_analysis()
        self.stipend_analysis()
        self.demand_analysis()
        self.correlation_analysis()
        self.create_visualizations()
        self.generate_report()

        print("\n🎉 EDA Analysis Complete!")
        print("Check the generated files for detailed insights and visualizations.")


def main():
    """Main function to run EDA"""
    print("Internship Demand Analytics - Exploratory Data Analysis")
    print("=" * 60)

    # Initialize EDA
    eda = InternshipEDA()

    if eda.df is not None:
        # Run full analysis
        eda.run_full_analysis()
    else:
        print("❌ Failed to load data. Please check the file path.")


if __name__ == "__main__":
    main()