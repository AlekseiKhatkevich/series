# Generated by Django 3.1 on 2020-08-31 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0063_auto_20200813_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subtitles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('episode_number', models.PositiveSmallIntegerField(verbose_name='Number of the episode')),
                ('text', models.TextField(verbose_name='Subtitles text')),
                ('language', models.CharField(choices=[('ab', 'Abkhaz'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), ('an', 'Aragonese'), ('hy', 'Armenian'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('bm', 'Bambara'), ('ba', 'Bashkir'), ('eu', 'Basque'), ('be', 'Belarusian'), ('bn', 'Bengali'), ('bh', 'Bihari'), ('bi', 'Bislama'), ('bs', 'Bosnian'), ('br', 'Breton'), ('bg', 'Bulgarian'), ('my', 'Burmese'), ('ca', 'Catalan; Valencian'), ('ch', 'Chamorro'), ('ce', 'Chechen'), ('ny', 'Chichewa; Chewa; Nyanja'), ('zh', 'Chinese'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('dv', 'Divehi; Maldivian;'), ('nl', 'Dutch'), ('dz', 'Dzongkha'), ('en', 'English'), ('eo', 'Esperanto'), ('et', 'Estonian'), ('ee', 'Ewe'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'Finnish'), ('fr', 'French'), ('ff', 'Fula'), ('gl', 'Galician'), ('ka', 'Georgian'), ('de', 'German'), ('el', 'Greek, Modern'), ('gn', 'Guaraní'), ('gu', 'Gujarati'), ('ht', 'Haitian'), ('ha', 'Hausa'), ('he', 'Hebrew (modern)'), ('hz', 'Herero'), ('hi', 'Hindi'), ('ho', 'Hiri Motu'), ('hu', 'Hungarian'), ('ia', 'Interlingua'), ('id', 'Indonesian'), ('ie', 'Interlingue'), ('ga', 'Irish'), ('ig', 'Igbo'), ('ik', 'Inupiaq'), ('io', 'Ido'), ('is', 'Icelandic'), ('it', 'Italian'), ('iu', 'Inuktitut'), ('ja', 'Japanese'), ('jv', 'Javanese'), ('kl', 'Kalaallisut'), ('kn', 'Kannada'), ('kr', 'Kanuri'), ('ks', 'Kashmiri'), ('kk', 'Kazakh'), ('km', 'Khmer'), ('ki', 'Kikuyu, Gikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz, Kyrgyz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', 'Korean'), ('ku', 'Kurdish'), ('kj', 'Kwanyama, Kuanyama'), ('la', 'Latin'), ('lb', 'Luxembourgish'), ('lg', 'Luganda'), ('li', 'Limburgish'), ('ln', 'Lingala'), ('lo', 'Lao'), ('lt', 'Lithuanian'), ('lu', 'Luba-Katanga'), ('lv', 'Latvian'), ('gv', 'Manx'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), ('ml', 'Malayalam'), ('mt', 'Maltese'), ('mi', 'Māori'), ('mr', 'Marathi (Marāṭhī)'), ('mh', 'Marshallese'), ('mn', 'Mongolian'), ('na', 'Nauru'), ('nv', 'Navajo, Navaho'), ('nb', 'Norwegian Bokmål'), ('nd', 'North Ndebele'), ('ne', 'Nepali'), ('ng', 'Ndonga'), ('nn', 'Norwegian Nynorsk'), ('no', 'Norwegian'), ('ii', 'Nuosu'), ('nr', 'South Ndebele'), ('oc', 'Occitan'), ('oj', 'Ojibwe, Ojibwa'), ('cu', 'Old Church Slavonic'), ('om', 'Oromo'), ('or', 'Oriya'), ('os', 'Ossetian, Ossetic'), ('pa', 'Panjabi, Punjabi'), ('pi', 'Pāli'), ('fa', 'Persian'), ('pl', 'Polish'), ('ps', 'Pashto, Pushto'), ('pt', 'Portuguese'), ('qu', 'Quechua'), ('rm', 'Romansh'), ('rn', 'Kirundi'), ('ro', 'Romanian, Moldavan'), ('ru', 'Russian'), ('sa', 'Sanskrit (Saṁskṛta)'), ('sc', 'Sardinian'), ('sd', 'Sindhi'), ('se', 'Northern Sami'), ('sm', 'Samoan'), ('sg', 'Sango'), ('sr', 'Serbian'), ('gd', 'Scottish Gaelic'), ('sn', 'Shona'), ('si', 'Sinhala, Sinhalese'), ('sk', 'Slovak'), ('sl', 'Slovene'), ('so', 'Somali'), ('st', 'Southern Sotho'), ('es', 'Spanish; Castilian'), ('su', 'Sundanese'), ('sw', 'Swahili'), ('ss', 'Swati'), ('sv', 'Swedish'), ('ta', 'Tamil'), ('te', 'Telugu'), ('tg', 'Tajik'), ('th', 'Thai'), ('ti', 'Tigrinya'), ('bo', 'Tibetan'), ('tk', 'Turkmen'), ('tl', 'Tagalog'), ('tn', 'Tswana'), ('to', 'Tonga'), ('tr', 'Turkish'), ('ts', 'Tsonga'), ('tt', 'Tatar'), ('tw', 'Twi'), ('ty', 'Tahitian'), ('ug', 'Uighur, Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('uz', 'Uzbek'), ('ve', 'Venda'), ('vi', 'Vietnamese'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('cy', 'Welsh'), ('wo', 'Wolof'), ('fy', 'Western Frisian'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang, Chuang'), ('zu', 'Zulu')], max_length=2, verbose_name='Subtitles language')),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtitles', to='archives.seasonmodel', verbose_name='Season')),
            ],
            options={
                'verbose_name': 'Subtitle',
                'verbose_name_plural': 'Subtitles',
                'permissions': (('permissiveness', 'Allow any action'),),
            },
        ),
        migrations.AddConstraint(
            model_name='subtitles',
            constraint=models.CheckConstraint(check=models.Q(language__in=('ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'en', 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gl', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'ia', 'id', 'ie', 'ga', 'ig', 'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'ky', 'kv', 'kg', 'ko', 'ku', 'kj', 'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'gv', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'nb', 'nd', 'ne', 'ng', 'nn', 'no', 'ii', 'nr', 'oc', 'oj', 'cu', 'om', 'or', 'os', 'pa', 'pi', 'fa', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'sa', 'sc', 'sd', 'se', 'sm', 'sg', 'sr', 'gd', 'sn', 'si', 'sk', 'sl', 'so', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'ta', 'te', 'tg', 'th', 'ti', 'bo', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'wo', 'fy', 'xh', 'yi', 'yo', 'za', 'zu')), name='lng_check'),
        ),
        migrations.AlterUniqueTogether(
            name='subtitles',
            unique_together={('season', 'episode_number', 'language')},
        ),
    ]
