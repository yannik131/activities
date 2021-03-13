{% load i18n %}

const categories = {
    //Neuroticism
    'anx': "{% trans 'Ängstlichkeit' %}", //anxiety
    'ang': "{% trans 'Reizbarkeit' %}", //anger
    'dep': "{% trans 'Depression' %}", //depression
    'con': "{% trans 'Soziale Befangenheit' %}", //self-consciousness
    'imm': "{% trans 'Impulsivität' %}", //immoderation
    'vul': "{% trans 'Verletzlichkeit' %}", //vulnerability
    
     //Extraversion
    'fri': "{% trans 'Herzlichkeit' %}", //friendliness
    'gre': "{% trans 'Geselligkeit' %}", //gregariousness
    'ass': "{% trans 'Durchsetzungsfähigkeit' %}", //assertiveness
    'act': "{% trans 'Aktivität' %}", //activity level
    'exc': "{% trans 'Erlebnishunger' %}", //excitement-seeking
    'che': "{% trans 'Frohsinn' %}", //cheerfulness
    
     //Openness
    'ima': "{% trans 'Fantasie' %}", //imagination
    'art': "{% trans 'Ästhetik' %}", //artistik interests
    'emo': "{% trans 'Gefühle' %}", //emotionality
    'adv': "{% trans 'Abenteuer' %}", //adventurousness
    'int': "{% trans 'Intellekt' %}", //intellect
    'lib': "{% trans 'Liberalität' %}", //liberalism

     //Agreeableness
    'tru': "{% trans 'Vertrauen' %}", //trust
    'mor': "{% trans 'Moralität' %}", //morality
    'alt': "{% trans 'Altruismus' %}", //altruism
    'coo': "{% trans 'Kooperativität' %}", //cooperation
    'mod': "{% trans 'Bescheidenheit' %}", //modesty
    'sym': "{% trans 'Gutherzigkeit' %}", //sympathy

    //Conscientiousness
    'eff': "{% trans 'Kompetenz' %}", //self-efficacy
    'ord': "{% trans 'Ordentlichkeit' %}", //orderliness
    'dut': "{% trans 'Pflichtbewusstsein' %}", //dutifulness
    'ach': "{% trans 'Leistungsstreben' %}", //achievement-striving
    'dis': "{% trans 'Selbstdisziplin' %}", //self-discipline
    'cau': "{% trans 'Besonnenheit' %}" //cautiousness
}