"""Shared presentation helpers; no changes to the model's scoring rules."""
import json
import pandas as pd

BASE_WEIGHTS = {'Economic need':30.0, 'Fresh food access':25.0, 'Resource gap':25.0, 'Potential reach':5.0}


def attach_service_status(schools, service):
    result = schools.copy()
    status = service.set_index('School ID')['Service status']
    result['Service status'] = result['School ID'].map(status).fillna('Not listed as served')
    result.loc[result['Already served'].fillna('').str.lower().eq('yes'), 'Service status'] = 'Currently served'
    return result


def export_with_context(frame, weights, snapshot):
    result = frame.copy()
    result['Model snapshot'] = snapshot
    result['Scenario weights (85-point scale)'] = json.dumps(weights, sort_keys=True)
    return result.to_csv(index=False).encode('utf-8')


def review_brief(schools, weights, snapshot, filters):
    lines = ['# Philadelphia School Food Access — Review Brief', '',
             f'Model snapshot: {snapshot}. These are saved observations, not live availability.',
             f'Schools in this shortlist: {len(schools)}.', '', '## Selection',
             *[f'- {name}: {", ".join(values) if values else "All"}' for name, values in filters.items()],
             '', '## Normalized scenario weights',
             *[f'- {name}: {value:.2f} points' for name, value in weights.items()],
             '', '## School shortlist',
             '| Scenario rank | School | Type / level | Score /85 | Service status |',
             '| ---: | --- | --- | ---: | --- |']
    def clean(value):
        return str(value).replace('|', '/').replace('\n',' ')
    for _,row in schools.iterrows():
        lines.append(f"| {row['Scenario rank']} | {clean(row['School'])} | {clean(row['Type'])} / {clean(row['Level'])} | {row['Scenario score']:.1f} | {clean(row['Service status'])} |")
    lines += ['', '## Interpretation and next actions',
              '- Rank is relative to the citywide eligible comparison pool; shared scores can share a rank.',
              '- Need scores do not measure proven program benefit. Enrollment is potential reach, not participation.',
              '- Confirm service status, produce availability, recurring hours, and access before making commitments.',
              '- Fresh-access scoring currently covers listed USDA supermarkets/superstores. Broader produce-outlet coverage is pending verified data.',
              '- Download the original workbook and source references from Methodology & Sources.']
    return '\n'.join(lines).encode('utf-8')


def weighted_components(row, weights):
    fields = [('Economic need','Economic points',30), ('Fresh food access','Fresh points',25),
              ('Resource gap','Resource points',25), ('Potential reach','Reach points',5)]
    return pd.DataFrame([{'Component':name, 'Baseline points':row[field], 'Scenario contribution':row[field]/maximum*weights[name], 'Current maximum':weights[name]} for name,field,maximum in fields])
