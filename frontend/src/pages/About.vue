<script setup lang="ts">
import { useGettext } from 'vue3-gettext'
const { $gettext } = useGettext()
</script>

<template>
  <div class="container">
    <h1>{{ $gettext('What\'s the Damage') }}</h1>
    <p>{{ $gettext('This tool is designed to process your bank account transactions in CSV files. It categorizes the transactions and generate insightful reports.') }}</p>
    <p>{{ $gettext('Efforts were made to be able to customize the behavior and potentially work with any CSV format finance companies may produce.') }}</p>

    <h2>{{ $gettext('The problem it solves') }}</h2>
    <p>{{ $gettext('While my bank service provider provides reports about my finances they are not detailed enough, hence this tool was created to give more insights.') }}</p>
    <p>{{ $gettext('Also my financial details are a private matter between myself and my chosen bank. To process my bank account exports, I need a solution that ensures only I have access to the data.') }}</p>
    <p class="bg-status-warning text-on-dark px-3 py-2 rounded">{{ $gettext('This application does not keep or sell any of your data. All uploaded content is removed as soon as the cache is expired. Cache is only used for your convenience.') }}</p>

    <h2>{{ $gettext('Main Features') }}</h2>
    <ul>
      <li><strong>{{ $gettext('Automated Categorization:') }}</strong> {{ $gettext('Categorizes transactions into well-known accounting categories such as deposits, payments, grocery, etc.') }}</li>
      <li><strong>{{ $gettext('Filtering:') }}</strong> {{ $gettext('Filter transactions by start and end dates, or group them by month for a comprehensive overview of your finances.') }}</li>
      <li><strong>{{ $gettext('Reporting:') }}</strong> {{ $gettext('Generate summarized reports that provide insights into your spending habits, grouped by transaction categories.') }}</li>
      <li><strong>{{ $gettext('Pivot table:') }}</strong> {{ $gettext('View your transactions in a pivot table format, allowing you to analyze your spending patterns and trends over time.') }}</li>
    </ul>

    <h2>{{ $gettext('The technical problem of categorizing transactions') }}</h2>
    <p>{{ $gettext('The very heart of the application is the categorization of transactions.') }}</p>
    <p>{{ $gettext('The transaction metadata while it contains useful information, is often incomplete or inconsistent. The most valuable information, the merchant identifier, is the least reliable to count on.') }}
      {{ $gettext('There is no formal requirements imposed by service providers about its format and its value can be changed at any time by merchants.') }}</p>
    <p>{{ $gettext('Another significant drawback is that merchant identifiers are quite variable, so there are no rules of thumb to follow.') }}</p>

    <p>{{ $gettext('The application provides several categorization technologies to solve this problem.') }}</p>

    <h3>{{ $gettext('The most reliable') }}</h3>
    <p>{{ $gettext('The application by default uses a ruleset which completely ignores merchant information and only considers the transaction type and the mathematical sign of the amounts.') }}
      {{ $gettext('While this method is considered stable, it provides less insights and can only distinguish a limited number of categories.') }} <u>{{ $gettext('This method is recommended only for quick setups.') }}</u></p>

    <h3>{{ $gettext('The most accurate') }}</h3>
    <p>{{ $gettext('The most accurate categorization results can be achieved using regular expressions which also takes into account the merchant identifier.') }}
      {{ $gettext('However creating and maintaining these rules is a time-consuming process and requires deeper technical knowledge.') }}
      {{ $gettext('Additionally, the rulesets are not easily shareable with other users.') }} <u>{{ $gettext('This method is recommended only for experienced users.') }}</u></p>

    <h3>{{ $gettext('The most advanced') }}</h3>
    <p>{{ $gettext('The application can use a Machine Learning model for categorization. Such models are trained on tens of thousands of transactions and can categorize transactions into a wide range of categories.') }}
       {{ $gettext('The advantage is that it need less maintenance and provides many more categories.') }}
       {{ $gettext('The disadvantage is that - depending on the size of the data used for training - there may be transactions that fall into the \'Other\' category.') }} <u>{{ $gettext('This method is currently unavailable for general use.') }}</u></p>

    <h2>{{ $gettext('Resources') }}</h2>
    <ul>
      <li>{{ $gettext('For the source code and documentation visit the GitHub repository of') }} <a href="https://github.com/abalage/whatsthedamage">{{ $gettext('whatsthedamage') }}</a></li>
      <li>{{ $gettext('To read about how this tool was made, please visit the') }} <a href="https://balagetech.com/introducing-whatsthedamage-to-process-your-bank-account-exports/">{{ $gettext('Introducing whatsthedamage to process your bank account exports') }}</a> {{ $gettext('blog post.') }}</li>
    </ul>
  </div>
</template>
