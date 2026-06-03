-- Override dbt's default schema naming so that +schema: staging resolves
-- to the schema named "staging" directly, rather than "<profile_schema>_staging".
-- Without this macro, dbt would concatenate the profile schema with the model
-- schema, producing names like "main_staging" or "staging_marts".
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
