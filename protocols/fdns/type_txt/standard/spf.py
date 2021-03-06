#Module to analyze spf standard of the txt-type records.
import protocols.fdns.type_txt.txt as txt

def get_df_spf(path):
    """
    Get a dataframe fdns records txt-type with spf standard. The meaning of new attributes is: A = mechanism "A" 
    on the query domain, MX = mechanism "MX" on the query domain, PTR = mechanism "PTR" on the query domain,
    A_REFERENCE_DOMAIN = evaluation of the "A" record about a specified domain, MX_REFERENCE_DOMAIN = evaluation of
    the "MX" record about a specified domain, PTR_REFERENCE_DOMAIN = evaluation of the "PTR" record about a specified
    domain, IP4_ADDRESS = authorized ip4 address to send mail from the query domain, IP4_MECHANISM = A, MX, PTR mechanism
    about specified ip4 address, IP4_QUALIFIERS = qualifiers referred to the ip4 address, IP6_ADDRESS = authorized ip6
    address to send mail from the query domain, IP6_MECHANISM = A, MX, PTR mechanism about specified ip6 address,
    IP6_QUALIFIERS = qualifiers referred to the ip6 address, INCLUDE =  SPF record to check, EXISTS = evaluation of the "A"
    record about a specified domain, REDIRECT = modifier to evaluate the record txt of specified domain, EXPLANATION = modifier
    to view the explanation string about the fault at specified domain, ALL_QUALIFIERS = qualifiers referred to the
    "ALL" mechanism. More informations at the link: https://tools.ietf.org/html/rfc7208#page-16.
  
        :param path: string contains the FDNS-TXT database path
        :return df_spf: Dataframe_spf object
    """
    NEW_ATTRIBUTE_LST = ['A', 'MX', 'PTR', 'A_REFERENCE_DOMAIN', 'MX_REFERENCE_DOMAIN', 'PTR_REFERENCE_DOMAIN', 'IP4_ADDRESS',
                         'IP4_MECHANISM', 'IP4_QUALIFIERS', 'IP6_ADDRESS', 'IP6_MECHANISM', 'IP6_QUALIFIERS', 'INCLUDE',
                        'EXISTS', 'REDIRECT', 'EXPLANATION', 'ALL_QUALIFIERS']
    NAN = txt.fdns.handle.math.nan
    attr_default_value = {'INCLUDE' : NAN, 'ALL_QUALIFIERS' : '+', 'EXISTS' : NAN, 'REDIRECT' :  NAN,
                          'A_REFERENCE_DOMAIN' : NAN, 'MX_REFERENCE_DOMAIN' : NAN, 'PTR_REFERENCE_DOMAIN' : NAN,
                          'EXPLANATION' :  NAN}
    df_txt = txt.get_df_txt(path)
    df_spf = txt.fdns.handle.get_df_rows_filtered(df_txt, 'Value', 'v=spf1', False, 1)
    df_spf = txt.fdns.handle.get_df_attributes_added(df_spf, NEW_ATTRIBUTE_LST , str)
    for index, item in enumerate(df_spf['Value']):
        field_list = item.split(" ")
        if not field_list[0].endswith(('}','all')) and item.endswith('}'):
            df_spf = get_df_mechanism_extracted(df_spf, field_list, index)
            df_spf = get_df_ip_info_extracted(df_spf, item, field_list, index, 'ipv4')
            df_spf = get_df_ip_info_extracted(df_spf, item, field_list, index, 'ipv6')                
            include_domains = txt.fdns.handle.re.findall(r'(?<=include:).*?(?= )', item)
            all_qualifier = txt.fdns.handle.re.search(r'(?<= ).(?=all})', item)
            exists_domains = txt.fdns.handle.re.findall(r'(?<=exists:).*?(?= )', item)
            redirect_domains = txt.fdns.handle.re.findall(r' redirect=(.*)}', item)
            a_reference_domains = txt.fdns.handle.re.findall(r'(?<= )[+-~?]?a:.*?(?= )', item)
            ptr_reference_domains = txt.fdns.handle.re.findall(r'(?<= )[+-~?]?ptr:.*?(?= )', item)
            mx_reference_domains = txt.fdns.handle.re.findall(r'(?<= )[+-~?]?mx:.*?(?= )', item)
            explanation_domain = txt.fdns.handle.re.search(r'(?<= )exp:.*?(?= )', item)
            attr_value_lst = [include_domains, all_qualifier, exists_domains, redirect_domains, a_reference_domains,
                         mx_reference_domains,  ptr_reference_domains, explanation_domain]
            df_spf = txt.get_df_new_values_assigned(df_spf, index, attr_value_lst, attr_default_value)         
    df_spf.drop(['Value'], axis = 1, inplace = True)
    return df_spf


def get_df_mechanism_extracted(df_spf, split_string, index_loop):
    """
    Get a dataframe with new three attributes referred to query domain mechanism. They are filled by attribute "Value"
    in df_spf.
    
        :param df_spf: Dataframe_spf object
        :param split_string: string list object taken by split the df_spf "Value" attribute
        :param index_loop: int value uses to iterate the df_spf
        :return df_spf: Dataframe_spf object
    """
    REGEX_STR = r"^([+-~?]?a)$|^([+-~?]?mx)$|^([+]?ptr)$"
    tmp_list_mechanism = []
    try: 
        first_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[1])
        if first_mechanism:
            tmp_list_mechanism.append(first_mechanism.group())
        second_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[2])
        if second_mechanism:
            tmp_list_mechanism.append(second_mechanism.group())
        third_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[3])
        if third_mechanism:
            tmp_list_mechanism.append(third_mechanism.group()) 
    except:
        pass
    for index, item in enumerate(tmp_list_mechanism):
        if item:
            if txt.fdns.handle.re.match(r'^([+-~?]?a)$', item):
                df_spf.at[index_loop, 'A'] = tmp_list_mechanism[index]
            if txt.fdns.handle.re.match(r'^([+-~?]?mx)$', item):
                df_spf.at[index_loop, 'MX'] = tmp_list_mechanism[index]
            if txt.fdns.handle.re.match(r'^([+]?ptr)$', item):
                df_spf.at[index_loop, 'PTR'] = tmp_list_mechanism[index]
    return df_spf          


def get_df_ip_info_extracted(df_spf, string_df_value, split_string, index_loop, ip_version):
    """
    Get a dataframe with new three attributes referred to specified ip-addresses. They are filled by attribute "Value"
    in df_spf. New attributes are create according to the ip_version ("ipv4" or "ipv6").
    
        :param df_spf: Dataframe_spf object
        :param string_df_value: string object taken by "Value" attribute in df_spf
        :param split_string: string list object taken by split the df_spf "Value" attribute
        :param index_loop: int value uses to iterate the df_spf
        :param ip_version: string object which must be "ipv4" or "ipv6"
        :return df_spf: Dataframe_spf object
    """
    REGEX_STR = r"^([+-~?]?a)$|^([+-~?]?mx)$|^([+]?ptr)$"
    if ip_version == 'ipv4':
        VERSION_1 = 'ip4:'
        VERSION_2 = 'IP4_'
    else:
        VERSION_1 = 'ip6:'
        VERSION_2 = 'IP6_'
    ip_complete_strings = txt.fdns.handle.re.findall(r"([+-~?]?" + VERSION_1 + ".*?) ", string_df_value)
    ip_qualifiers = txt.fdns.handle.re.findall(r"([+-~?]?)" + VERSION_1, string_df_value)
    ip_addresses = txt.fdns.handle.re.findall(r"[+-~?]?" + VERSION_1 + "(.*?) ", string_df_value)
    if ip_complete_strings:
        list_qualifiers = []
        tmp_list_mechanism = []
        list_mechanism = []
        for index, item in enumerate(ip_complete_strings):
            if not ip_qualifiers[index]:
                list_qualifiers.append('+')
            else:
                list_qualifiers.append(ip_qualifiers[index])
            try:
                first_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[split_string.index(item) + 1])
                if first_mechanism:
                    tmp_list_mechanism.append(first_mechanism)
                second_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[split_string.index(item) + 2])
                if second_mechanism:
                    tmp_list_mechanism.append(second_mechanism)
                third_mechanism = txt.fdns.handle.re.match(REGEX_STR, split_string[split_string.index(item) + 3])
                list_mechanism.append(tmp_list_mechanism)
            except:
                pass
        df_spf.at[index_loop, VERSION_2 + 'ADDRESS'] = ip_addresses
        df_spf.at[index_loop, VERSION_2 + 'MECHANISM'] = list_mechanism
        df_spf.at[index_loop, VERSION_2 + 'QUALIFIERS'] = list_qualifiers
    return df_spf        
            
            