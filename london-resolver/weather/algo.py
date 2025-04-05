def has_verified_metrics(df):
    return  df.loc[(df['qod_score'] >= 0.999) & (df['pol_score'] > 0) & (df['temperature'] > -40) & (df['temperature'] < 80)] 
